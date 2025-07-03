import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatThread, ChatMessage

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thread_id = self.scope['url_route']['kwargs']['thread_id']
        self.room_group_name = f'chat_{self.thread_id}'
        print(f"WebSocket connected for thread {self.thread_id}")
        print(f"User: {self.scope.get('user')}")
        print(f"User authenticated: {self.scope.get('user').is_authenticated}")

        # User check
        if not self.scope['user'].is_authenticated:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"WebSocket disconnected from thread {self.thread_id}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'chat_message')

            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'delete_message':
                await self.handle_delete_message(data)
        except json.JSONDecodeError:
            print("Error: Invalid JSON received")
        except KeyError as e:
            print(f"Error: Missing key in received data - {e}")

    async def handle_chat_message(self, data):
        message = data['message']
        sender_id = data['sender_id']
        reply_to_id = data.get('reply_to_id')
        temp_id = data.get('temp_id')

        # Save message to DB
        msg_obj = await self.save_message(sender_id, message, reply_to_id)
        if not msg_obj:
            return

        # Broadcast message to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': sender_id,
                'sender_name': msg_obj['sender_name'],
                'timestamp': msg_obj['timestamp'],
                'msg_id': msg_obj['msg_id'],
                'reply_to': msg_obj['reply_to'],
                'temp_id': temp_id,  # Pass temp_id back
            }
        )

    async def handle_delete_message(self, data):
        msg_id = data.get('msg_id')
        sender_id = self.scope['user'].id

        if not msg_id:
            return

        deleted = await self.delete_message_from_db(msg_id, sender_id)

        if deleted:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message_deleted',
                    'msg_id': msg_id,
                }
            )

    async def chat_message(self, event):
        print(f"Broadcasting message: {event}")
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp'],
            'msg_id': event['msg_id'],
            'reply_to': event['reply_to'],
            'temp_id': event.get('temp_id'),  # Include temp_id in response
        }))

    async def message_deleted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_deleted',
            'msg_id': event['msg_id']
        }))

    @database_sync_to_async
    def save_message(self, sender_id, message, reply_to_id):
        try:
            print(f"Attempting to save message: sender_id={sender_id}, message='{message}', reply_to_id={reply_to_id}")
            sender = User.objects.get(id=sender_id)
            print(f"Found sender: {sender}")
            thread = ChatThread.objects.get(id=self.thread_id)
            print(f"Found thread: {thread}")
            reply_to = None
            if reply_to_id:
                try:
                    reply_to = ChatMessage.objects.get(id=reply_to_id)
                    print(f"Found reply_to: {reply_to}")
                except ChatMessage.DoesNotExist:
                    reply_to = None
                    print("Reply message not found")
            msg = ChatMessage.objects.create(
                thread=thread,
                sender=sender,
                content=message,
                reply_to=reply_to
            )
            print(f"Message created successfully: {msg}")
            return {
                'msg_id': msg.id,
                'sender_name': sender.get_full_name() or sender.username,
                'timestamp': msg.timestamp.strftime('%H:%M'),
                'reply_to': {
                    'id': reply_to.id,
                    'content': reply_to.content,
                    'sender_name': reply_to.sender.get_full_name() or reply_to.sender.username
                } if reply_to else None
            }
        except User.DoesNotExist:
            print(f"Error: sender with id {sender_id} not found.")
            return None
        except ChatThread.DoesNotExist:
            print(f"Error: chat thread with id {self.thread_id} not found.")
            return None
        except Exception as e:
            print(f"Error saving message: {e}")
            return None

    @database_sync_to_async
    def delete_message_from_db(self, msg_id, sender_id):
        try:
            message = ChatMessage.objects.get(id=msg_id, sender_id=sender_id)
            message.delete()
            print(f"Message {msg_id} deleted by user {sender_id}")
            return True
        except ChatMessage.DoesNotExist:
            print(f"Message {msg_id} not found or user {sender_id} is not the sender.")
            return False
        except Exception as e:
            print(f"Error deleting message {msg_id}: {e}")
            return False

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_authenticated:
            self.group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'type': event.get('type', 'info')
        })) 