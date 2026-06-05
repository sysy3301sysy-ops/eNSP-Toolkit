# 🔧 eNSP Toolkit — 华为网络设备配置生成器

> 快速生成华为设备（AR路由器 / S5700交换机 / 4G LTE）的 eNSP 配置脚本
> 专为网络工程课设、实验、竞赛设计

---

## ✨ 功能

| 模板 | 设备 | 适用场景 |
|------|------|---------|
| `router-basic` | AR路由器 | 基础接口IP + 静态路由 |
| `router-ospf` | AR路由器 | OSPF 单区域配置 |
| `switch-vlan` | S5700交换机 | VLAN划分 + Trunk + Access |
| `dhcp-server` | AR路由器 | DHCP服务器 + 地址池 |
| `nat-easyip` | AR路由器 | EasyIP NAT 上网配置 |
| `4g-lte-basic` | 通用 | eNodeB/MME/SPGW 框架 |

## 快速开始

```bash
# 克隆或下载
git clone https://github.com/<你的用户名>/eNSP-Toolkit.git
cd eNSP-Toolkit

# 运行（无需任何第三方库，纯 Python 标准库）
python ensp_config_gen.py interactive
```

Windows 用户也可以直接双击 `run.bat` 启动。

## 📋 使用演示

```
$ python ensp_config_gen.py interactive

============================================================
  🔧 eNSP 华为设备配置生成器
============================================================
...

  选择模板 (输入 key，如 switch-vlan): switch-vlan

  设备名: SW-CORE
  VLAN列表,逗号分隔: 10,20,30
  Access接口: GE0/0/1
  Access接口VLAN: 10
  Trunk接口: GE0/0/24
  Trunk允许VLAN: 10,20,30

  ✅ 生成完成！
  ...
  📁 已保存到: config_switch-vlan_SW-CORE.txt
```

## 🎯 适合谁

- 网络工程/网络优化专业的学生
- 正在做 eNSP 课设的人
- 备考华为认证（HCIA/HCIP）的考生
- 需要快速搭建网络实验环境的人

## 💡 贡献

提 issue 或 PR，让工具支持更多模板。

## 📄 许可

MIT License

---

**如果这个工具帮到了你，欢迎 ⭐ 投喂支持 ❤️**
