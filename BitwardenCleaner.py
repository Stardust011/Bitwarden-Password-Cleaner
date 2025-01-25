from urllib.parse import urlsplit, urlunsplit  # 导入 urlparse、urlsplit 和 urlunsplit 函数
import json
import re
from rich import print
from rich.panel import Panel
import requests
import tldextract

from rich.traceback import install
install(show_locals=True)

# 文件名常量
input_file_name = "bitwarden_export.json"  # 将此替换为从 Bitwarden 导出的文件
output_file_name = f"{input_file_name.replace('.json', '_output.json')}"
deleted_file_name = f"{input_file_name.replace('.json', '_deleted.json')}"
check_file_name = f"{input_file_name.replace('.json', '_check.json')}"

# 从输入文件加载数据
with open(input_file_name, 'r', encoding='utf-8') as input_file:
    data = json.load(input_file)

# 初始化变量
processed_items = 0
total_items = len(data['items'])
duplicates = {}  # 将此行更改为将 duplicates 初始化为字典
deleted_items = []
ip_address_pattern = r'\b(?:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d{1,5})?)\b'

def add_https_to_uri(uri):
    # 检查 URI 是否有 scheme
    # 检查 uri 中是否有 ://
    if "://" in uri:
        return uri
    return add_https_to_uri("https://" + uri)

def get_netloc(url):
    url_split = urlsplit(url)
    return url_split.netloc

def get_final_redirect_url(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        return response.url
    except requests.exceptions.RequestException as e:
        print(f"[yellow]访问超时: {e}")
        return None

def is_url_reachable(url):
    try:
        response = requests.head(f"{url}", allow_redirects=True, timeout=5)
        return True
    except requests.exceptions.RequestException as e:
        print(f"[yellow]访问超时: {url}, 错误: {e}")
        return False

def DoH_query(hostname):
    url = "https://1.1.1.1/dns-query"
    headers = {
        "accept": "application/dns-json",
    }

    params_ipv4 = {
        "name": hostname,
        "type": "A",
    }
    params_ipv6 = {
        "name": hostname,
        "type": "AAAA",
    }

    response = requests.get(url, params=params_ipv4, headers=headers)
    flag = False

    if response.status_code == 200:
        data = response.json()
        if "Answer" in data:
            for answer in data["Answer"]:
                if "data" in answer:
                    print(f"[green]> 找到解析: {answer}")
                    flag = True
        else:
            print("[yellow]未找到 IPv4 地址解析, 尝试 IPv6 地址解析")
            response = requests.get(url, params=params_ipv6, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if "Answer" in data:
                    for answer in data["Answer"]:
                        if "data" in answer:
                            print(f"[green]> 找到解析: {answer}")
                            flag = True
                else:
                    print(f"[yellow]未找到 IPv6 地址解析")
            else:
                print(f"[bright_red]DNS 请求失败, 状态码: {response.status_code}")
                exit(1)
    else:
        print(f"[bright_red]DNS 请求失败, 状态码: {response.status_code}")
        exit(1)
    return flag

def get_valid_url(uri):
    # 如果 uri 为空
    if not uri:
        return None, f"uri 为空"
    
    uri_parts = urlsplit(uri)
    scheme, netloc, path, _, _ = uri_parts
    clean_uri = urlunsplit((scheme, netloc, path, '', ''))
    
    if netloc == '':
        print(f"[red]netloc 为空: {clean_uri}")
        return None, f"netloc 为空: {clean_uri}"
    
    print(f"[green]> 处理: {scheme} {netloc} {path}")

    if re.match(ip_address_pattern, netloc) is not None:
        print(f"[green]> 匹配 IP 地址: {clean_uri}")
        return clean_uri, None
    print(f"> 非 IP 地址, 检查网页可达性: {netloc}")
    
    if is_url_reachable(clean_uri):
        print(f"> 网址可达: {clean_uri}")
        # 尝试获取最终重定向地址
        redirect_uri = get_final_redirect_url(clean_uri)
        if redirect_uri:
            print(f"> 找到重定向地址: {redirect_uri}")
            # 清理重定向地址
            redirect_uri_parts = urlsplit(redirect_uri)
            scheme, netloc, path, _, _ = redirect_uri_parts
            clean_uri = urlunsplit((scheme, netloc, path, '', ''))
            print(f"> 清理后的地址: {clean_uri}")
        return clean_uri, None
    print(f"[yellow]> 网址不可达: {clean_uri}")
    # DNS over HTTPS 查询
    print(f"> 执行 DoH 查询: {uri_parts.hostname}")
    if DoH_query(uri_parts.hostname):
        print(f"> 存在 DNS 记录: {uri_parts.hostname}")
        return clean_uri, None
    print(f"[yellow]> 不存在 DNS 记录: {uri_parts.hostname}")
    ext = tldextract.extract(uri)
    print(f"[yellow]> 尝试查询 TLD DNS 记录: {ext.registered_domain}")
    if DoH_query(ext.registered_domain):
        print(f"> 存在 DNS 记录: {ext.registered_domain}")
        return clean_uri, None

    return None, f"网站不可达且不存在 DNS 记录: {uri_parts.hostname}"

items_copy = data['items'][:]
items_ready_for_write = []
items_need_check = []
items_deleted = []

def add_items_to_write(item):
    items_ready_for_write.append(item)

if __name__ == "__main__":
    # 处理每一个项目
    for i, item in enumerate(items_copy):
        processed_items = i + 1
        item_name = item['name']
        # 检查 item_name 是否有 /
        if '/' in item_name:
            print(f"[yellow]> 项目名称中有 /: {item_name}")
            item_name = add_https_to_uri(item_name)
            name_part = urlsplit(item_name).netloc
            # 如果 name_part 为空
            if not name_part:
                print(f"[red]> 跳过项目，因为名称部分为空: {item_name}")
                item['notes'] = f"跳过项目，因为名称部分为空: {item_name}"
                items_need_check.append(item)
                continue
            # 更新 item_name
            item_name = name_part
            print(f"[yellow]> 更新项目名称: {item_name}")
        print(f"[bright_white]处理项目 ({processed_items}/{total_items}): {item_name}")

        # 检查项目是否有 "login" 字段
        if 'login' not in item or not isinstance(item['login'], dict):
            print("[red]> 没有 login 字段, 跳过")
            item['notes'] = "没有 login 字段"
            items_need_check.append(item)
            continue

        uris = item['login']['uris']
        username = item['login']['username']
        password = item['login']['password']

        # 快速去重，检查 items_ready_for_write 中是否已经存在相同的 item_name，username，password 项目
        if items_ready_for_write:
            flag = False
            for item_ready in items_ready_for_write:
                if item_ready['name'] == item_name and item_ready['login']['username'] == username and item_ready['login']['password'] == password:
                    print(f"[red]> 删除项目，因为它是重复的: {item_name}")
                    item['notes'] = f"重复项: {item_ready['name']}"
                    items_deleted.append(item)
                    flag = True
                    break
            if flag:
                continue

        # 确保 uris, username 和 password 不为 None
        if uris is None or username is None or password is None:
            print("[yellow]> 跳过项目，因为缺少数据")
            item['notes'] = "跳过项目，因为缺少数据"
            items_need_check.append(item)
            continue

        corrected_uris = []
        for uri_data in uris:
            uri = uri_data['uri']

            if uri is None:
                print(f"[red]> 一条记录的 uri 为空")
                continue

            url = add_https_to_uri(uri)
            uri_parts = urlsplit(url)
            scheme, netloc, path, _, _ = uri_parts        
            if not netloc:
                # 如果网站为空, 跳过
                print(f"[red]> 跳过项目，因为 Netloc 为空: {uri}")
                continue
            clean_uri = urlunsplit((scheme, netloc, path, '', ''))
            # 验证地址是否有效
            valid_uri, error_word = get_valid_url(clean_uri)
            if valid_uri is None:
                print(f"[yellow]> 跳过项目，因为 URI 无效: {clean_uri}")
                continue
            else:
                corrected_uris.append({"uri": valid_uri})
                continue

        reason_for_deletion = ""
        if len(corrected_uris) == 0:
            reason_for_deletion = "所有 URI 都无效"
            item['notes'] = "所有 URI 都无效"
            print(f"[red]> 删除项目，因为所有 URI 都无效: {item_name}")
            items_deleted.append(item)
            continue

        item['login']['uris'] = corrected_uris
        item_name = get_netloc(corrected_uris[0]['uri'])
        print(f"[green]> 更新项目名称: {item_name}")
        # 去重
        if items_ready_for_write:
            flag = False
            for item_ready in items_ready_for_write:
                if item_ready['name'] == item_name and item_ready['login']['username'] == username and item_ready['login']['password'] == password:
                    print(f"[red]> 删除项目，因为是重复的: {item_name}")
                    item['notes'] = f"重复项: {item_ready['name']}"
                    items_deleted.append(item)
                    flag = True
                    break
            if flag:
                continue
        print(f"[green]> 添加项目到写入列表: {item_name}")
        add_items_to_write(item)

    # 保存最终数据，包括更新和删除的项目
    data['items'] = items_ready_for_write
    with open(output_file_name, 'w') as output_file:
        json.dump(data, output_file, indent=2)

    with open(deleted_file_name, 'w') as deleted_file:
        json.dump(items_deleted, deleted_file, indent=2)

    with open(check_file_name, 'w') as check_file:
        json.dump(items_need_check, check_file, indent=2)

    print(f"处理了 {processed_items} 个项目，共 {total_items} 个。")
    print(f"删除的项目: {len(items_deleted)}")
    print(f"需要检查的项目: {len(items_need_check)}")
    print(f"输出文件: {output_file_name}")
    print(f"删除文件: {deleted_file_name}")
    print(f"检查文件: {check_file_name}")