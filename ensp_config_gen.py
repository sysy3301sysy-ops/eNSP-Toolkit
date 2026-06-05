#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eNSP 华为设备配置生成器 v1.0
==============================
快速生成华为 AR/交换机的 eNSP 基础配置脚本。
适合课设、实验、比赛场景。

用法:
  python ensp_config_gen.py interactive    # 交互式生成
  python ensp_config_gen.py template       # 打印可用模板

Windows 用户如果遇到乱码: chcp 65001
"""

import os
import sys
from datetime import datetime
from typing import Optional


# ==============================================================
#  模板库
# ==============================================================

TEMPLATES = {
    "router-basic": {
        "desc": "AR路由器 - 基础配置 (接口IP + 静态路由)",
        "device": "AR",
        "prompts": {
            "hostname": "设备名",
            "interface": "上行接口 (如 GE0/0/0)",
            "ip": "接口IP (如 192.168.1.1 24)",
            "static_net": "静态路由目标网段 (如 10.0.0.0)",
            "static_mask": "静态路由掩码 (如 255.0.0.0)",
            "static_next": "下一跳IP",
        },
    },
    "router-ospf": {
        "desc": "AR路由器 - OSPF 单区域配置",
        "device": "AR",
        "prompts": {
            "hostname": "设备名",
            "router_id": "Router-ID (如 1.1.1.1)",
            "area": "OSPF区域 (默认 0)",
            "networks": "宣告网段,逗号分隔 (如 192.168.1.0 0.0.0.255,10.0.0.0 0.0.0.255)",
        },
    },
    "switch-vlan": {
        "desc": "S5700交换机 - VLAN + Trunk + Access 配置",
        "device": "S5700",
        "prompts": {
            "hostname": "设备名",
            "vlans": "VLAN列表,逗号分隔 (如 10,20,30)",
            "access_port": "Access接口 (如 GE0/0/1)",
            "access_vlan": "Access接口VLAN (如 10)",
            "trunk_port": "Trunk接口 (如 GE0/0/24)",
            "trunk_vlans": "Trunk允许VLAN (如 10,20,30)",
        },
    },
    "dhcp-server": {
        "desc": "AR路由器 - DHCP服务器配置",
        "device": "AR",
        "prompts": {
            "hostname": "设备名",
            "gateway": "网关IP (如 192.168.10.1)",
            "mask": "子网掩码 (如 255.255.255.0)",
            "dns1": "首选DNS (如 114.114.114.114)",
            "dns2": "备选DNS (如 8.8.8.8)",
            "pool_start": "地址池起始 (如 192.168.10.100)",
            "pool_end": "地址池结束 (如 192.168.10.200)",
            "lease_days": "租期天数 (默认 1)",
            "excluded": "排除地址,逗号分隔 (可选)",
        },
    },
    "nat-easyip": {
        "desc": "AR路由器 - EasyIP NAT (内网转外网上网)",
        "device": "AR",
        "prompts": {
            "hostname": "设备名",
            "inside_if": "内网接口 (如 GE0/0/1)",
            "inside_net": "内网网段 (如 192.168.10.0)",
            "inside_mask": "内网掩码 (如 255.255.255.0)",
            "outside_if": "外网接口 (如 GE0/0/0)",
            "acl_num": "ACL编号 (如 2000)",
        },
    },
    "4g-lte-basic": {
        "desc": "4G LTE基础 - eNodeB / MME / SPGW 配置框架",
        "device": "通用",
        "prompts": {
            "enb_name": "eNodeB名称",
            "enb_id": "eNodeB ID (数字)",
            "mcc": "MCC (中国 460)",
            "mnc": "MNC (中国移动 00 / 联通 01 / 电信 11)",
            "tac": "TAC (跟踪区码)",
            "mme_ip": "MME IP地址",
            "cell_id": "小区ID",
        },
    },
}


# ==============================================================
#  生成函数
# ==============================================================

def gen_router_basic(values: dict) -> str:
    h, iface, ip = values["hostname"], values["interface"], values["ip"]
    sn, sm, snh = values["static_net"], values["static_mask"], values["static_next"]
    return f"""#
system-view
sysname {h}
#
interface {iface}
 undo shutdown
 ip address {ip}
#
ip route-static {sn} {sm} {snh}
#
save
y
"""


def gen_router_ospf(values: dict) -> str:
    h, rid, area = values["hostname"], values["router_id"], values["area"]
    nets = [n.strip() for n in values["networks"].split(",") if n.strip()]
    lines = [f"""#
system-view
sysname {h}
#
ospf 1 router-id {rid}
 area {area}"""]

    for net in nets:
        parts = net.split()
        if len(parts) >= 2:
            lines.append(f"  network {parts[0]} {parts[1]}")
        else:
            lines.append(f"  network {net} 0.0.0.0")
    lines.append("#")
    lines.append("save")
    lines.append("y")
    return "\n".join(lines)


def gen_switch_vlan(values: dict) -> str:
    h = values["hostname"]
    vlans = [v.strip() for v in values["vlans"].split(",") if v.strip()]
    ap, av = values["access_port"], values["access_vlan"]
    tp, tv = values["trunk_port"], values["trunk_vlans"]
    lines = [f"""#
system-view
sysname {h}
#"""]
    for v in vlans:
        lines.append(f"vlan batch {v}")
    lines.append(f"""#
interface {ap}
 port link-type access
 port default vlan {av}
#
interface {tp}
 port link-type trunk
 port trunk allow-pass vlan {tv}
#
save
y
""")
    return "\n".join(lines)


def gen_dhcp_server(values: dict) -> str:
    h = values["hostname"]
    gw, mask = values["gateway"], values["mask"]
    dns1, dns2 = values["dns1"], values["dns2"]
    ps, pe = values["pool_start"], values["pool_end"]
    days = values.get("lease_days", "1")
    excluded = values.get("excluded", "").strip()

    # 从网关中计算网段
    gw_parts = gw.split(".")
    network_base = f"{gw_parts[0]}.{gw_parts[1]}.{gw_parts[2]}.0"

    lines = [f"""#
system-view
sysname {h}
#
dhcp enable
#
ip pool pool1
 gateway-list {gw}
 network {network_base} mask {mask}
 dns-list {dns1} {dns2}
 lease day {days}
"""]
    if excluded:
        for eip in excluded.split(","):
            eip = eip.strip()
            if eip:
                lines.append(f" excluded-ip-address {eip}")
    lines.append(f"""#
interface Vlanif1
 ip address {gw} {mask}
 dhcp select global
#
save
y
""")
    return "\n".join(lines)


def gen_nat_easyip(values: dict) -> str:
    h = values["hostname"]
    inside_if, inside_net, inside_mask = values["inside_if"], values["inside_net"], values["inside_mask"]
    outside_if, acl_num = values["outside_if"], values["acl_num"]

    # 内网网关 (取网段 .1)
    gw_parts = inside_net.split(".")
    gateway = f"{gw_parts[0]}.{gw_parts[1]}.{gw_parts[2]}.1"

    return f"""#
system-view
sysname {h}
#
acl {acl_num}
 rule 5 permit source {inside_net} {inside_mask}
#
interface {outside_if}
 undo shutdown
 ip address dhcp-alloc
 nat outbound {acl_num}
#
interface {inside_if}
 undo shutdown
 ip address {gateway} 255.255.255.0
#
save
y
"""


def gen_4g_lte(values: dict) -> str:
    """生成4G LTE基础配置框架 (eNodeB/MME/SPGW示意)"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    enb = values["enb_name"]
    enb_id = values["enb_id"]
    mcc = values["mcc"]
    mnc = values["mnc"]
    tac = values["tac"]
    mme_ip = values["mme_ip"]
    cell_id = values["cell_id"]

    return f"""# ==========================================================
# 4G LTE 基础配置框架
# 适用设备: 华为 eNodeB / MME / SPGW
# 生成时间: {now}
# ==========================================================

#
# ---- eNodeB 侧配置 ----
#
system-view
sysname {enb}
#
enb-id {enb_id}
#
mcc {mcc}
mnc {mnc}
tac {tac}
#
# 小区配置
cell
 cell-id {cell_id}
 物理小区标识 1
 频点 100          (根据实际频段调整)
 带宽 20           (20MHz)
#
# S1 接口 (连接MME)
interface S1
 mme-peer {mme_ip} port 36412
#
# X2 接口 (连接相邻eNodeB)
interface X2
#  neighbor-enb <neighbor_enb_id> ip <neighbor_ip>
#

# ---- MME 侧配置参考 ----
#
! MME 配置 (示意)
! mme-id 1
! 支持TAI: {mcc}-{mnc}-{tac}
! pool:
!   apn cmnet
!   dns 114.114.114.114
!
# ---- SPGW 侧配置参考 ----
#
! SPGW 配置 (示意)
! apn cmnet
! pdntype IPv4
! qci 9 (Non-GBR)
! ue-ambr uplink 100Mbps downlink 100Mbps
#
save
y
"""


# 生成函数映射
GENERATORS = {
    "router-basic": gen_router_basic,
    "router-ospf": gen_router_ospf,
    "switch-vlan": gen_switch_vlan,
    "dhcp-server": gen_dhcp_server,
    "nat-easyip": gen_nat_easyip,
    "4g-lte-basic": gen_4g_lte,
}


# ==============================================================
#  交互式界面
# ==============================================================

def list_templates():
    """列出所有可用模板"""
    print()
    print("=" * 60)
    print("  [eNSP Toolkit] 可用模板")
    print("=" * 60)
    for key, tpl in TEMPLATES.items():
        print(f"\n  [{key}]")
        print(f"      设备: {tpl['device']}")
        print(f"      说明: {tpl['desc']}")
        for pname, pdesc in tpl['prompts'].items():
            if pname == "hostname":
                continue
            print(f"      参数: {pname} -> {pdesc}")
    print("=" * 60)


def interactive_mode():
    """交互式配置生成"""
    print()
    print("=" * 60)
    print("  [eNSP Toolkit] 华为设备配置生成器")
    print("=" * 60)
    list_templates()

    tname = input("\n  [?] 选择模板 (输入key, 如 switch-vlan): ").strip().lower()
    if tname not in TEMPLATES:
        print(f"\n  [x] 未知模板: {tname}")
        return

    tpl = TEMPLATES[tname]
    print(f"\n  已选: {tpl['desc']}")
    print("-" * 40)

    values = {}
    for pname, pdesc in tpl['prompts'].items():
        val = input(f"  {pdesc}: ").strip()
        if not val:
            # 设置默认值
            defaults = {
                "area": "0",
                "lease_days": "1",
                "excluded": "",
                "networks": "",
            }
            val = defaults.get(pname, "")
        values[pname] = val

    generator = GENERATORS.get(tname)
    if not generator:
        print(f"\n  [x] 该模板暂无生成函数")
        return

    config = generator(values)

    print()
    print("=" * 60)
    print("  [OK] 生成完成! 配置如下:")
    print("=" * 60)
    print(config)

    # 保存文件
    fname = f"config_{tname}_{values.get('hostname', 'unknown').replace(' ', '_')}.txt"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(config)
    print(f"  [FILE] 已保存到: {os.path.abspath(fname)}")
    print("=" * 60)


# ==============================================================
#  入口
# ==============================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd in ("interactive", "i"):
            interactive_mode()
        elif cmd in ("template", "templates", "list", "l"):
            list_templates()
        else:
            print(f"未知命令: {cmd}")
            print("用法: python ensp_config_gen.py interactive  交互式生成")
            print("      python ensp_config_gen.py list         列出模板")
    else:
        interactive_mode()
