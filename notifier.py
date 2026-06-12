# -*- coding: utf-8 -*-
"""
通用通知模块

按通道拆分独立环境变量（参考之前 DINGTALK_WEBHOOK/DINGTALK_SECRET 的取值风格）：

| 通道 (type)       | 环境变量                                                                     |
|-------------------|------------------------------------------------------------------------------|
| qmsg              | PUSH_QMSG_KEY                                                                |
| pushplus          | PUSH_PUSHPLUS_TOKEN                                                          |
| server            | PUSH_SERVER_KEY                                                              |
| workWechatRobot   | PUSH_WORK_WECHAT_ROBOT_KEY                                                   |
| workWechat        | PUSH_WORK_WECHAT_CORPID + PUSH_WORK_WECHAT_CORP_SECRET + PUSH_WORK_WECHAT_AGENT_ID |

凡是配置了对应环境变量的通道，都会在签到完成后被推送一次。
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from push import PushSender, parse


# 通道 -> 单一 key 的环境变量名（key 为字符串的通道）
SINGLE_KEY_CHANNELS: Dict[str, str] = {
    'qmsg': 'PUSH_QMSG_KEY',
    'pushplus': 'PUSH_PUSHPLUS_TOKEN',
    'server': 'PUSH_SERVER_KEY',
    'workWechatRobot': 'PUSH_WORK_WECHAT_ROBOT_KEY',
}


def format_quota(quota: int) -> str:
    """格式化额度显示"""
    if quota >= 1000000:
        return f'{quota / 1000000:.2f}M'
    elif quota >= 1000:
        return f'{quota / 1000:.2f}K'
    else:
        return str(quota)


def _build_summary_lines(results: List[Dict[str, Any]]) -> List[str]:
    """生成汇总文本（用于消息末尾）"""
    total = len(results)
    success_count = len([r for r in results if r.get('success')])
    fail_count = total - success_count

    if fail_count == 0:
        return [f'全部成功 ✨ ({success_count}/{total})']
    elif success_count == 0:
        return [f'全部失败 ⚠️ ({fail_count}/{total})']
    else:
        return [f'成功 {success_count}，失败 {fail_count}']


def build_checkin_content(results: List[Dict[str, Any]], execution_time: str) -> List[Dict[str, Any]]:
    """
    构建结构化签到报告内容，可被 push.parse 转换为 markdown / html / txt。
    """
    success_list = [r for r in results if r.get('success')]
    fail_list = [r for r in results if not r.get('success')]

    content: List[Dict[str, Any]] = [
        {'h1': {'content': '📋 NewAPI 签到报告'}},
        {'txt': {'content': f'执行时间：{execution_time}'}},
    ]

    if success_list:
        content.append({'h2': {'content': f'✅ 成功 ({len(success_list)}个)'}})
        rows = [['账号', '奖励', '详情']]
        for r in success_list:
            name = r.get('name', '未知账号')
            quota = r.get('quota_awarded', 0)
            quota_str = f'+{format_quota(quota)}' if quota else '-'
            checkin_count = r.get('checkin_count')
            detail = f'已签 {checkin_count} 天' if checkin_count else r.get('message', '成功')
            rows.append([name, quota_str, detail])
        content.append({'table': {'contents': rows}})

    if fail_list:
        content.append({'h2': {'content': f'❌ 失败 ({len(fail_list)}个)'}})
        rows = [['账号', '原因']]
        for r in fail_list:
            name = r.get('name', '未知账号')
            message = r.get('message', '未知错误')
            if (r.get('session_expired')
                    or 'session' in message.lower()
                    or '认证' in message
                    or '过期' in message):
                message = f'⚠️ {message}'
            rows.append([name, message])
        content.append({'table': {'contents': rows}})

    summary = _build_summary_lines(results)
    content.append({'h3': {'content': '汇总'}})
    for line in summary:
        content.append({'txt': {'content': line}})

    expired = [
        r for r in fail_list
        if r.get('session_expired')
        or 'session' in r.get('message', '').lower()
        or '认证' in r.get('message', '')
        or '过期' in r.get('message', '')
    ]
    if expired:
        content.append({
            'blockQuote': {
                'content': '⚠️ 注意：部分账号 Session 已失效，请及时更新 Cookie！'
            }
        })

    return content


def _load_push_configs() -> List[Dict[str, Any]]:
    """
    从环境变量收集所有已配置的推送通道。

    每个通道一组独立环境变量（参考钉钉 DINGTALK_WEBHOOK 风格）：
    - PUSH_QMSG_KEY                  -> qmsg
    - PUSH_PUSHPLUS_TOKEN            -> pushplus
    - PUSH_SERVER_KEY                -> server
    - PUSH_WORK_WECHAT_ROBOT_KEY     -> workWechatRobot
    - PUSH_WORK_WECHAT_CORPID + PUSH_WORK_WECHAT_CORP_SECRET +
      PUSH_WORK_WECHAT_AGENT_ID      -> workWechat
    """
    configs: List[Dict[str, Any]] = []

    for push_type, env_name in SINGLE_KEY_CHANNELS.items():
        key = os.environ.get(env_name, '').strip()
        if key:
            configs.append({'type': push_type, 'key': key})

    corpid = os.environ.get('PUSH_WORK_WECHAT_CORPID', '').strip()
    corp_secret = os.environ.get('PUSH_WORK_WECHAT_CORP_SECRET', '').strip()
    agent_id = os.environ.get('PUSH_WORK_WECHAT_AGENT_ID', '').strip()
    if corpid and corp_secret and agent_id:
        configs.append({
            'type': 'workWechat',
            'key': {
                'corpid': corpid,
                'corpSecret': corp_secret,
                'agentid': agent_id,
            },
        })

    return configs


def doSend(title: str, message, configs: Optional[List[Dict[str, Any]]] = None) -> bool:
    """
    通用推送入口。

    Args:
        title: 消息标题
        message: 字符串或结构化内容列表（push.tools.parse 可识别）
        configs: 推送配置列表（不传则从环境变量收集）

    Returns:
        是否至少尝试推送过一个通道
    """
    print(f'{title}: {message if isinstance(message, str) else "[结构化内容]"}')

    if isinstance(message, str):
        message = [
            {'h1': {'content': title}},
            {'txt': {'content': message}},
        ]

    if configs is None:
        configs = _load_push_configs()

    if not configs:
        print('[通知] 未配置任何 PUSH_* 环境变量，跳过推送')
        return False

    parsed_md = parse(message, template='markdown')
    sent_any = False

    for cfg in configs:
        push_type = cfg.get('type', '')
        key = cfg.get('key', '')
        try:
            sender = PushSender(push_type, key)
            extra = {k: v for k, v in cfg.items() if k not in ('type', 'key')}
            sender.send(parsed_md, title=title, **extra)
            sent_any = True
        except Exception as e:
            print(f'[通知] 通道 {push_type} 推送失败：{e}')

    return sent_any


def send_checkin_notification(
    results: List[Dict[str, Any]],
    execution_time: Optional[str] = None,
) -> bool:
    """
    发送签到通知（统一入口，供 checkin.py 调用）。
    """
    configs = _load_push_configs()
    if not configs:
        print('[通知] 未配置任何 PUSH_* 环境变量，跳过通知')
        return False

    if not execution_time:
        execution_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    success_count = len([r for r in results if r.get('success')])
    fail_count = len(results) - success_count
    if fail_count == 0:
        title = f'✅ 签到成功 ({success_count}个账号)'
    elif success_count == 0:
        title = f'❌ 签到失败 ({fail_count}个账号)'
    else:
        title = f'📋 签到完成 (成功{success_count}/失败{fail_count})'

    content = build_checkin_content(results, execution_time)
    return doSend(title, content, configs=configs)


# 测试入口
if __name__ == '__main__':
    test_results = [
        {
            'name': '主力站',
            'success': True,
            'message': '签到成功',
            'quota_awarded': 500000,
            'checkin_count': 15,
        },
        {
            'name': '备用站',
            'success': True,
            'message': '签到成功',
            'quota_awarded': 100000,
            'checkin_count': 8,
        },
        {
            'name': '测试站',
            'success': False,
            'message': 'Session 已过期',
            'session_expired': True,
        },
    ]

    preview = parse(
        build_checkin_content(test_results, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        template='markdown',
    )
    print('=== Markdown 预览 ===')
    print(preview)
    print('====================')

    if _load_push_configs():
        send_checkin_notification(test_results)
    else:
        print('\n提示：设置以下任一组环境变量后可测试实际推送：')
        print('  - PUSH_QMSG_KEY=xxx')
        print('  - PUSH_PUSHPLUS_TOKEN=xxx')
        print('  - PUSH_SERVER_KEY=xxx')
        print('  - PUSH_WORK_WECHAT_ROBOT_KEY=xxx')
        print('  - PUSH_WORK_WECHAT_CORPID + PUSH_WORK_WECHAT_CORP_SECRET + PUSH_WORK_WECHAT_AGENT_ID')
