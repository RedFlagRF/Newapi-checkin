#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloudflare 绕过模块

借鉴 newapi-auto-checkin Chrome 扩展的思路：
- 检测 CF 拦截（403 + HTML 验证页面）
- 使用 Playwright 无头浏览器自动过 CF 验证
- 获取 cf_clearance cookie 和 session 后回退到 requests 完成签到

两种模式映射：
  Chrome 扩展: service worker fetch → CF 拦截 → 标签页执行
  本项目:      requests 直连 → CF 拦截 → Playwright 无头浏览器
"""

import os
import re
import time
from typing import Optional, Tuple


def detect_cloudflare_block(status_code: int, response_text: str) -> Tuple[bool, str]:
    """
    检测 Cloudflare 拦截

    借鉴 background.js:153-156 的检测逻辑：
    - 403 + "Just a moment" / <!DOCTYPE html>
    - 非 JSON 响应包含 <!DOCTYPE 标签

    Args:
        status_code: HTTP 状态码
        response_text: 响应文本

    Returns:
        (is_blocked, reason): 是否被 CF 拦截及原因描述
    """
    if status_code == 403:
        if 'Just a moment' in response_text or 'just a moment' in response_text.lower():
            return True, 'Cloudflare JS Challenge (403 + Just a moment)'
        if '<!DOCTYPE html' in response_text.lower() and 'cloudflare' in response_text.lower():
            return True, 'Cloudflare HTML Challenge (403 + Cloudflare page)'

    if status_code == 503:
        if 'cloudflare' in response_text.lower() and ('challenge' in response_text.lower() or 'checking your browser' in response_text.lower()):
            return True, 'Cloudflare Challenge (503)'

    try:
        import json
        json.loads(response_text)
    except (json.JSONDecodeError, ValueError):
        if '<!DOCTYPE' in response_text and ('Just a moment' in response_text or 'challenge-platform' in response_text or 'cf-challenge' in response_text):
            return True, 'Cloudflare Challenge (non-JSON HTML response)'

    return False, ''


class CloudflareBypasser:
    """
    使用 Playwright 无头浏览器绕过 Cloudflare 防护

    对应 Chrome 扩展的 "标签页执行模式":
    - 在真实浏览器环境中加载目标站点
    - 等待 CF 验证完成（自动解决 JS Challenge）
    - 提取 cf_clearance cookie 和 session cookie
    - 返回给 requests 继续完成签到
    """

    def __init__(self, base_url: str, session_cookie: str = None, user_id: str = None):
        self.base_url = base_url.rstrip('/')
        self.session_cookie = session_cookie
        self.user_id = user_id
        self._playwright_available = self._check_playwright()

    def _check_playwright(self) -> bool:
        try:
            from playwright.sync_api import sync_playwright
            return True
        except ImportError:
            return False

    def is_available(self) -> bool:
        return self._playwright_available

    def bypass_and_get_cookies(self, timeout: int = 60) -> Optional[dict]:
        """
        使用 Playwright 绕过 CF 并提取所有需要的认证信息

        对应 Chrome 扩展的 autoOAuthLogin + captureAuthHeaders 流程

        Returns:
            dict 包含:
            - session: session cookie 值
            - cf_clearance: cf_clearance cookie 值
            - user_id: 从 localStorage 提取的用户 ID（如果有）
            或者 None 表示失败
        """
        if not self._playwright_available:
            print('[CF 绕过] Playwright 未安装，无法绕过 Cloudflare')
            return None

        print(f'[CF 绕过] 使用 Playwright 访问 {self._mask_url(self.base_url)}...')
        from playwright.sync_api import sync_playwright

        result = None
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                    ]
                )

                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                )

                if self.session_cookie:
                    domain = self.base_url.replace('https://', '').replace('http://', '').split('/')[0]
                    context.add_cookies([
                        {
                            'name': 'session',
                            'value': self.session_cookie,
                            'domain': domain,
                            'path': '/',
                        }
                    ])

                page = context.new_page()

                print('[CF 绕过] 正在加载页面并等待 CF 验证...')
                page.goto(self.base_url, wait_until='networkidle', timeout=timeout * 1000)

                for attempt in range(3):
                    current_url = page.url
                    title = page.title()
                    print(f'[CF 绕过] 尻试 {attempt + 1}: URL={current_url[:80]}, Title={title[:50]}')

                    is_cf_challenge = (
                        'Just a moment' in title or
                        'Checking your browser' in title or
                        'challenge' in current_url.lower() or
                        page.locator('#challenge-running, .cf-challenge-running').count() > 0
                    )

                    if is_cf_challenge:
                        print(f'[CF 绕过] CF 验证页面，等待自动解决 ({attempt + 1}/3)...')
                        page.wait_for_load_state('networkidle', timeout=30000)
                        time.sleep(5)
                    else:
                        break

                cookies = context.cookies()
                cookie_dict = {}
                for c in cookies:
                    cookie_dict[c['name']] = c['value']

                result = {}

                if 'session' in cookie_dict:
                    result['session'] = cookie_dict['session']
                    print('[CF 绕过] 已提取 session cookie')
                elif self.session_cookie:
                    result['session'] = self.session_cookie
                    print('[CF 绕过] 使用原有 session cookie')

                if 'cf_clearance' in cookie_dict:
                    result['cf_clearance'] = cookie_dict['cf_clearance']
                    print('[CF 绕过] 已提取 cf_clearance cookie')

                try:
                    user_data = page.evaluate('() => localStorage.getItem("user")')
                    if user_data:
                        import json
                        user_obj = json.loads(user_data)
                        if 'id' in user_obj:
                            result['user_id'] = str(user_obj['id'])
                            print(f'[CF 绕过] 已提取 user_id')
                except Exception:
                    pass

                try:
                    page.goto(f'{self.base_url}/api/user/self', wait_until='networkidle', timeout=15000)
                    body = page.evaluate('() => document.body.innerText')
                    import json
                    data = json.loads(body)
                    if data.get('success') and data.get('data', {}).get('id'):
                        result['user_id'] = str(data['data']['id'])
                        result['session_valid'] = True
                        print('[CF 绕过] session 验证有效')
                except Exception:
                    pass

                browser.close()

            except Exception as e:
                print(f'[CF 绕过] Playwright 执行失败: {e}')
                try:
                    browser.close()
                except Exception:
                    pass
                return None

        if result and ('cf_clearance' in result or 'session' in result):
            print('[CF 绕过] 成功获取认证信息')
            return result
        else:
            print('[CF 绕过] 未获取到有效认证信息')
            return None

    def execute_checkin_in_browser(self, timeout: int = 60) -> Optional[dict]:
        """
        在浏览器中直接执行签到（对应 Chrome 扩展的 doCheckInRequest 标签页模式）

        用于 cf_clearance + requests 仍然失败时的终极回退方案

        Returns:
            签到结果 dict 或 None
        """
        if not self._playwright_available:
            return None

        print(f'[CF 绕过] 在浏览器中直接执行签到...')
        from playwright.sync_api import sync_playwright

        result = None
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
                )

                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                )

                domain = self.base_url.replace('https://', '').replace('http://', '').split('/')[0]

                if self.session_cookie:
                    context.add_cookies([
                        {'name': 'session', 'value': self.session_cookie, 'domain': domain, 'path': '/'}
                    ])

                page = context.new_page()
                page.goto(self.base_url, wait_until='networkidle', timeout=timeout * 1000)

                for _ in range(3):
                    title = page.title()
                    if 'Just a moment' in title:
                        page.wait_for_load_state('networkidle', timeout=30000)
                        time.sleep(5)
                    else:
                        break

                if self.user_id:
                    page.evaluate(f'() => localStorage.setItem("user", JSON.stringify({{"id": {self.user_id}}}))')

                api_result = page.evaluate('''async () => {
                    try {
                        const resp = await fetch('/api/user/checkin', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            credentials: 'include'
                        });
                        const text = await resp.text();
                        try {
                            const data = JSON.parse(text);
                            const success = data.success === true || data.status === 'success';
                            const msg = data.message || data.msg || '签到完成';
                            const msgStr = typeof msg === 'string' ? msg : JSON.stringify(msg);
                            const alreadyKeywords = ['已签到', '已经签到', 'already', '重复签到'];
                            const alreadyCheckedIn = !success && alreadyKeywords.some(k => msgStr.includes(k));
                            return {
                                success: success || alreadyCheckedIn,
                                alreadyCheckedIn: alreadyCheckedIn,
                                message: msgStr,
                                httpStatus: resp.status,
                                data: data
                            };
                        } catch(e) {
                            return { error: 'Response is not JSON: ' + text.substring(0, 100), httpStatus: resp.status, success: false };
                        }
                    } catch(e) {
                        return { error: e.message, success: false, httpStatus: 0 };
                    }
                }''')

                result = api_result
                print(f'[CF 绕过] 浏览器内签到结果: {result.get("message", result.get("error", "unknown"))}')

                browser.close()

            except Exception as e:
                print(f'[CF 绕过] 浏览器内签到失败: {e}')
                try:
                    browser.close()
                except Exception:
                    pass
                return None

        return result

    @staticmethod
    def _mask_url(url: str) -> str:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain_parts = parsed.netloc.split('.')
            if len(domain_parts) >= 2:
                masked_domain = f"{domain_parts[0]}.***." + '.'.join(domain_parts[-1:])
            else:
                masked_domain = '***'
            return f"{parsed.scheme}://{masked_domain}"
        except Exception:
            return 'https://***'