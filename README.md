# Bitwarden-Password-Cleaner

Bitwarden Password Cleaner 是一个用于清理和优化 Bitwarden 密码管理器导出文件的 Python 脚本。它可以删除重复条目，检查 URL 的有效性，并将清理后的数据导出到新的 JSON 文件中。

## 目录
- [功能](#功能)
- [先决条件](#先决条件)
- [快速开始](#快速开始)
- [使用方法](#使用方法)
- [贡献](#贡献)
- [许可证](#许可证)

## 功能

Bitwarden Password Cleaner 提供以下功能，帮助您清理和优化 Bitwarden 密码管理器导出文件：
- **删除重复条目**：自动识别并删除基于名称、URI、用户名和密码的重复条目。
- **URL 验证**：通过网络访问与DNS解析检查 Bitwarden 条目中的 URL 的有效性。如果 URL 不可达，则从条目的 URIs 列表中删除。
- **优化导出**：导出一个清理和优化后的 Bitwarden 导出 JSON 文件，删除重复条目和无效 URL。
- **实时输出**：实时显示进度，显示正在处理的项目和删除原因（如果有）。
- **详细的删除报告**：生成一个单独的 JSON 文件，包含有关删除项目的信息，包括删除原因，供您参考。
- **用户友好**：设计易于使用，提供清晰的说明和可定制的设置，以适应您的偏好。

## 先决条件

在开始之前，请确保您满足以下要求：

- 系统上安装了 Python 3.10 或更高版本。
- 一个 Bitwarden 密码管理器导出 JSON 文件。

## 快速开始

1. 将此存储库克隆到本地计算机：

   ```bash
   git clone https://github.com/Stardust011/Bitwarden-Password-Cleaner.git
   ```

2. 导航到项目目录：

   ```bash
   cd Bitwarden-Password-Cleaner
   ```

3. 安装所需的 Python 包：

   ```bash
   pip install rich requests tldextract
   ```

## 使用方法

要使用 Bitwarden Password Cleaner，请按照以下步骤操作：

1. 将您的 Bitwarden 导出 JSON 文件放在项目目录中。如您不想修改代码，可将文件重命名为`bitwarden_export.json`

2. (可选)打开 `bitwardenCleaner.py` 脚本，根据您的偏好配置文件名和其他设置。

3. 运行脚本：

   ```bash
   python BitwardenCleaner.py
   ```

4. 脚本将处理输入文件并生成三个输出文件：一个包含清理后的数据，一个包含删除的项目，还有一个是待您人工检查的项目，一般是账号或密码缺省。

## 贡献

欢迎贡献！如果您有任何建议、改进或错误修复，请打开一个 issue 或提交一个 pull request。

## 许可证

此项目根据 MIT 许可证授权。
