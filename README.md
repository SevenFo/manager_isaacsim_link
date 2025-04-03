# Isaac Sim 链接管理器

这个工具用于帮助创建和管理 Isaac Sim 扩展的符号链接，使 IDE 能够正确识别和提供代码补全。

## 功能

- 自动创建从 Isaac Sim 扩展目录 (`xxx/site-packages/isaacsim/exts/**`) 到 site-packages (`xxx/site-packages/isaacsim`) 的符号链接
- 安全移除先前创建的链接
- 保持链接记录，以便安全地管理链接生命周期

## 使用方法

### 创建链接

```bash
python manage_isaacsim_links.py --create
```

### 移除链接

```bash
python manage_isaacsim_links.py --remove
```

## 配置

使用前需要修改脚本顶部的配置部分：

1. 打开 `manage_isaacsim_links.py` 文件
2. 更新 `ISAACSIM_SITE_PACKAGES` 变量为您环境中的实际路径
3. `EXTS_DIR` 和 `LINK_RECORD_FILE` 会基于此路径自动推断

```python
# --- 配置 ---
# !! 修改为你环境中的实际路径 !!
ISAACSIM_SITE_PACKAGES = Path(
    "你的Isaac Sim环境的site-packages路径"
)
# -------------
```

## 注意事项

- **兼容性**：仅适用于通过 `pip` 安装的 `Isaac Sim 4.5`，并且只在 `Windows 11` 平台测试过
- 在 Windows 系统上，创建符号链接需要管理员权限或启用开发人员模式
- 创建链接后，可能需要重启 IDE 或重新加载 Python 语言服务才能生效
- 脚本会保存链接记录，以便安全地移除之前创建的符号链接
