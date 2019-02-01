import asyncio
import json
# import math
import re
from typing import List, Optional, Union, Dict, Collection, Any, Iterable

from aiocqhttp.message import Message, escape
from nonebot import on_command, CommandSession, IntentCommand
from nonebot import on_natural_language, NLPSession
from nonebot.helpers import context_id, render_expression as expr
from nonebot.session import BaseSession

from aki import nlp
from aki.aio import requests
from aki.log import logger
from . import expressions as e

__plugin_name__ = '智能聊天'

# key: context id, value: named entity type
tuling_sessions = {}


def tuling_ne_type(replies: List[str],
                   keywords: Dict[str, Collection[Any]]) -> Optional[str]:
    for reply in replies:
        for ne_type, ne_keywords in keywords.items():
            for kw in ne_keywords:
                if isinstance(kw, type(re.compile(''))):
                    match = bool(kw.search(reply))
                else:
                    match = kw in reply
                if match:
                    return ne_type


@on_command('tuling', aliases=('聊天', '对话'))
async def tuling(session: CommandSession):
    message = session.get('message', prompt=expr(e.I_AM_READY))

    ctx_id = context_id(session.ctx)
    if ctx_id in tuling_sessions:
        del tuling_sessions[ctx_id]

    tmp_msg = Message(message)
    text = tmp_msg.extract_plain_text()
    images = [s.data['url'] for s in tmp_msg
              if s.type == 'image' and 'url' in s.data]

    # call tuling api
    replies = await call_tuling_api(session, text, images)
    logger.debug(f'Got tuling\'s replies: {replies}')

    if replies:
        for reply in replies:
            await session.send(escape(reply))
            await asyncio.sleep(0.8)
    else:
        await session.send(expr(e.I_DONT_UNDERSTAND))

    one_time = session.state.get('one_time', False)
    if one_time:
        # tuling123 may opened a session, we should recognize the
        # situation that tuling123 want more information from the user.
        # for simplification, we only recognize named entities,
        # and since we will also check the user's input later,
        # here we can allow some ambiguity.
        ne_type = tuling_ne_type(replies, {
            'LOC': ('哪里', '哪儿', re.compile(r'哪\S城市'), '位置'),
            'TIME': ('什么时候',),
        })
        if ne_type:
            logger.debug(f'One time call, '
                         f'and there is a tuling session for {ne_type}')
            tuling_sessions[ctx_id] = ne_type
    else:
        session.pause()


@tuling.args_parser
async def _(session: CommandSession):
    if session.current_key == 'message':
        text = session.current_arg_text.strip()
        if ('拜拜' in text or '再见' in text) and len(text) <= 4:
            session.finish(expr(e.BYE_BYE))
            return
        session.state[session.current_key] = session.current_arg


@on_natural_language(only_to_me=False)
async def _(session: NLPSession):
    confidence = None  # by default we don't return result

    if session.ctx['to_me']:
        # if the user is talking to us, we may consider reply to him/her
        confidence = 60.0

    ctx_id = context_id(session.ctx)
    if ctx_id in tuling_sessions:
        ne_type = tuling_sessions[ctx_id]
        lex_result = await nlp.lexer(session.msg_text)
        # we only mind the first paragraph
        words = lex_result[0] if lex_result else []
        for w in words:
            if ne_type == w['ne']:
                # if there is a tuling session existing,
                # and the user's input is exactly what tuling wants,
                # we are sure that the user is replying tuling
                confidence = 100.0 - len(words) * 5.0
                break

    if confidence:
        return IntentCommand(confidence, 'tuling', args={
            'message': session.msg,
            'one_time': True
        })


# @on_natural_language(keywords={'聊', '说话'})
# async def _(session: NLPSession):
#     text = session.msg_text.strip()
#     confidence = 0.0
#     match = len(text) <= 4 and '陪聊' in text
#     if match:
#         confidence = 100.0
#     else:
#         score = await nlp.sentence_similarity('来陪我聊天', text)
#         if score > 0.70:
#             match = True
#             confidence = math.ceil(score * 10) * 10  # 0.74 -> 80.0
#
#     if match:
#         return NLPResult(confidence, 'tuling', {})


async def call_tuling_api(
        session: BaseSession,
        text: Optional[str],
        image: Optional[Union[List[str], str]]) -> List[str]:
    url = 'http://openapi.tuling123.com/openapi/api/v2'

    api_keys = session.bot.config.TULING_API_KEY
    if not isinstance(api_keys, Iterable) or isinstance(api_keys, str):
        api_keys = [api_keys]

    for api_key in api_keys:
        payload = {
            'reqType': 0,
            'perception': {},
            'userInfo': {
                'apiKey': api_key,
                'userId': context_id(session.ctx, use_hash=True)
            }
        }

        group_unique_id = context_id(session.ctx, mode='group', use_hash=True)
        if group_unique_id:
            payload['userInfo']['groupId'] = group_unique_id

        if image and not isinstance(image, str):
            image = image[0]

        if text:
            payload['perception']['inputText'] = {'text': text}
            payload['reqType'] = 0
        elif image:
            payload['perception']['inputImage'] = {'url': image}
            payload['reqType'] = 1
        else:
            return []

        try:
            resp = await requests.post(url, json=payload)
            if resp.ok:
                resp_payload = await resp.json()
                if resp_payload['intent']['code'] == 4003:  # 当日请求超限
                    continue
                if resp_payload['results']:
                    return_list = []
                    for result in resp_payload['results']:
                        res_type = result.get('resultType')
                        if res_type in ('text', 'url'):
                            return_list.append(result['values'][res_type])
                    return return_list
        except (requests.RequestException, json.JSONDecodeError,
                TypeError, KeyError):
            pass
    return []
