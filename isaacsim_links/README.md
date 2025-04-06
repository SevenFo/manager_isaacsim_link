# Isaac Sim Links

这个工具包为 Isaac Sim 和 Omni 扩展创建符号链接，极大地改善了在 IDE 中的代码自动补全和导航体验。

## 问题背景

Isaac Sim 和 Omni 扩展使用了特殊的目录结构，这导致 Python 解释器和 IDE（如 VS Code、PyCharm 等）无法找到正确的模块路径，从而无法提供代码补全、类型提示和导入建议等功能。

这个工具通过创建符号链接，将实际的代码路径链接到 Python 能够识别的标准导入路径位置，从而解决这个问题。

## 特性

- 自动扫描 `isaacsim.exts`、`isaacsim.extsPhysics` 和 `omni.extscore` 扩展
- 创建必要的符号链接以支持 IDE 代码补全
- 安装/卸载包时自动创建/删除链接
- 提供命令行工具手动管理链接
- 跨平台支持 (Windows、Linux、MacOS)

- 运行此工具后，IDE可以正确识别Isaac Sim的模块并提供代码补全：
    
    ![代码补全效果展示](../images/code_completion.gif)

## 安装

```bash
pip install isaacsim-links
```

安装后，符号链接将自动创建，无需额外操作。

## 使用

### 自动模式（推荐）

- **安装包时**：自动创建所有必要的符号链接。
- **卸载包时**：自动清理所有创建的符号链接。

### 手动命令

创建链接:
```bash
isaacsim-links --create
```

删除链接:
```bash
isaacsim-links --remove
```

## 注意事项

- 在 Windows 上使用时，可能需要管理员权限或启用开发人员模式。
- 对于非标准的 Isaac Sim 安装位置，可能需要修改代码中的路径配置。
- 创建链接后，可能需要重启 IDE 或重新加载 Python 语言服务器以使更改生效。

## 支持的扩展目录

- `isaacsim.exts`: Isaac Sim 标准扩展
- `isaacsim.extsPhysics`: Isaac Sim 物理扩展
- `omni.extscore`: Omni 核心扩展

## 许可证

MIT