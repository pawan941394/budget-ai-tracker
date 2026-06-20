from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import ChatSession, ChatMessage


def chat_sessions(request, username):
    sessions = ChatSession.objects.filter(username=username)
    data = []

    for session in sessions:
        messages = session.messages.all().values('role', 'content', 'created_at')
        data.append({
            'session_id': session.session_id,
            'username': session.username,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'message_count': session.messages.count(),
            'messages': [
                {
                    'role': msg['role'],
                    'content': msg['content'],
                    'timestamp': msg['created_at'].isoformat()
                }
                for msg in messages
            ]
        })

    return JsonResponse({'sessions': data})


def chat_session_detail(request, session_id):
    session = get_object_or_404(ChatSession, session_id=session_id)
    messages = session.messages.all().values('role', 'content', 'created_at')

    conversation = []
    for msg in messages:
        conversation.append({
            'role': msg['role'],
            'content': msg['content'],
            'timestamp': msg['created_at'].isoformat()
        })

    return JsonResponse({
        'session_id': session.session_id,
        'username': session.username,
        'created_at': session.created_at.isoformat(),
        'updated_at': session.updated_at.isoformat(),
        'conversation': conversation
    })


def chat_sessions_html(request, username):
    sessions = ChatSession.objects.filter(username=username)
    return render(request, 'ai_Chat_bot/chat_sessions.html', {'sessions': sessions})


def chat_session_html(request, session_id):
    session = get_object_or_404(ChatSession, session_id=session_id)
    messages = session.messages.all()
    return render(request, 'ai_Chat_bot/chat_detail.html', {'session': session, 'messages': messages})
