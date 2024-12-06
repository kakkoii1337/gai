# Gaimace Protocol

## Overview

This protocol outlines a framework for building a chat application using the NATS messaging system. It covers communication channels, message formats, and additional features like presence and typing indicators.

## Subjects (Channels)

### 1. Chat Rooms

-   Subject: chat.room.<room_id>
-   Used for public or group chat messages.

### 2. Direct Messages

-   Subject: chat.private.<user1_id>.<user2_id>
-   Used for sending private messages between two users.

### 3. Presence Notifications

-   Subject: presence.<user_id>
-   Used to broadcast user online/offline status.

### 4. Typing Indicators

-   Subject: typing.<room_id> or typing.<user1_id>.<user2_id>
-   Used to indicate when a user is typing a message.

## Message Formats

### 1. Chat Message

```json
{
    "type": "message",
    "sender": "<sender_id>",
    "dialogue_id": "<dialogue_id>",
    "recipient": "<recipient_id>",
    "timestamp": "2023-10-22T14:48:00Z",
    "content": "Hello!"
}
```

### 2. Presence Notification

```json
{
    "type": "presence",
    "user_id": "<user_id>",
    "status": "online"
}
```

### 3. Typing Indicator

```json
{
    "type": "typing",
    "user_id": "<user_id>",
    "status": "typing"
}
```

### 4. Typing Indicator (Group Chat)

```json
{
    "type": "typing",
    "user_id": "<user_id>",
    "status": "typing",
    "dialogue_id": "<dialogue_id>"
}
```

### 5. Error Message

```json
{
    "type": "error",
    "message": "Invalid request"
}
```

### 6. Read Receipt

```json
{
    "type": "read",
    "dialogue_id": "<dialogue_id>",
    "user_id": "<user_id>"
}
```

### 7. Agent Profile

```json
{
    "type": "profile",
    "user_id": "<user_id>",
    "name": "John Doe",
    "avatar": "https://example.com/avatar.jpg"
}
```

## Authentication and Authorization

-   Implement token-based authentication to secure the connection between clients and the NATS server.
-   Ensure authorization rules allow users to subscribe and publish to appropriate subjects only.

## Message Persistence

-   Use NATS JetStream or another storage solution to store messages for later retrieval.
-   Define policies for messages retention and history retrieval limits.

## Handling Disconnections

-   Consider implementing a timeout mechanism to queue messages for users who are temporarily disconnected.
-   Send a notification to others in the room or chat subject about the disconnection if needed.

## Additional Features

-   Add user-friendly features like emoji support, file sharing, and more by extending the message format.
-   Consider implementing a user directory for easy access to user IDs/names within Gai.
