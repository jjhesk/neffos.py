import json
import re
from datetime import datetime
from typing import Union

import websocket
from moody import Bolors
from websocket import WebSocketApp

# The OnNamespaceConnect is the event name that it's fired on before namespace connect.
from neffos.exceptions import replyError, isReplyErr, ErrInvalidPayload, ErrBadNamespace, ErrClosed, ErrBadRoom

OnNamespaceConnect = "_OnNamespaceConnect"
# The OnNamespaceConnected is the event name that it's fired on after namespace connect.
OnNamespaceConnected = "_OnNamespaceConnected"
# The OnNamespaceDisconnect is the event name that it's fired on namespace disconnected.
OnNamespaceDisconnect = "_OnNamespaceDisconnect"
# The OnRoomJoin is the event name that it's fired on before room join.
OnRoomJoin = "_OnRoomJoin"
# The OnRoomJoined is the event name that it's fired on after room join.
OnRoomJoined = "_OnRoomJoined"
# The OnRoomLeave is the event name that it's fired on before room leave.
OnRoomLeave = "_OnRoomLeave"
# The OnRoomLeft is the event name that it's fired on after room leave.
OnRoomLeft = "_OnRoomLeft"
# The OnAnyEvent is the event name that it's fired, if no incoming event was registered, it's a "wilcard".
OnAnyEvent = "_OnAnyEvent"
# The OnNativeMessage is the event name, which if registered on empty ("") namespace it accepts native messages(Message.Body and Message.IsNative is filled only).
OnNativeMessage = "_OnNativeMessage"

ackBinary = 'M'
ackIDBinary = 'A'
ackNotOKBinary = 'H'
waitIsConfirmationPrefix = '#'
waitComesFromClientPrefix = '$'
# The WSData is just a string type alias.
WSData = str
Namespaces = dict
# Map<string, MessageHandlerFunc>;
Events = dict


class NeffSupportSocket(websocket.WebSocketApp):
    OPEN: str = "OPEN"
    CLOSE: str = "CLOSED"
    readyState: str

    def __init__(self, url):
        super().__init__(
            url=url,
            on_open=self.f_open,
            on_close=self.f_close,
            on_data=self.f_data,
            on_error=self.f_err,
        )
        self.readyState = False

    def f_open(self, ws: WebSocketApp):
        self.readyState = NeffSupportSocket.OPEN
        self._open()

    def f_data(self, data, frameopcode, enabled):
        self._message(data)

    def f_err(self, err):
        pass

    def f_close(self, close_status_code: int, close_msg: str):
        self.readyState = NeffSupportSocket.CLOSE
        self._close(close_msg, close_status_code)

    def _open(self):
        pass

    def _close(self, msg, code):
        pass

    def _message(self, message):
        pass


class IRISSocket(websocket.WebSocketApp):
    # https://ethvigil.com/docs/websocket_api
    websocketMessagePrefix: str
    websocketStringMessageType: str
    websocketIntMessageType: str
    websocketBoolMessageType: str
    websocketJSONMessageType: str
    websocketMessageSeparator: str = ";"
    websocketMessagePrefixLen: int
    websocketMessageSeparatorLen: int
    websocketMessagePrefixAndSepIdx: int
    websocketMessagePrefixIdx: int
    websocketMessageSeparatorIdx: int
    isReady: bool = False

    def __init__(self, url):
        super().__init__(
            url=url,
            on_open=self.f_open,
            on_close=self.f_close,
            on_data=self.f_data,
            on_error=self.f_err,
        )
        self.websocketMessagePrefix = "iris-websocket-message"
        self.websocketStringMessageType = 0
        self.websocketIntMessageType = 1
        self.websocketBoolMessageType = 2
        self.websocketJSONMessageType = 4
        self.websocketMessageSeparator = ";"
        self.websocketMessagePrefixLen = len(self.websocketMessagePrefix)
        self.websocketMessageSeparatorLen = len(self.websocketMessageSeparator)
        self.websocketMessagePrefixAndSepIdx = self.websocketMessagePrefixLen + self.websocketMessageSeparatorLen - 1
        self.websocketMessagePrefixIdx = self.websocketMessagePrefixLen - 1
        self.websocketMessageSeparatorIdx = self.websocketMessageSeparatorLen - 1
        self.isReady = False

    def encodeMessage(self, event: str, data: any) -> str:
        m = data
        if isinstance(data, str):
            msgType = 0
        elif isinstance(data, bool):
            msgType = 2
        elif isinstance(data, int):
            msgType = 1
        elif isinstance(data, dict):
            msgType = 4
            m = json.dumps(data, sort_keys=True, separators=(',', ':'))
        else:
            msgType = 4
            m = data

        return self._msg(event, msgType, m)

    def _msg(self, event: str, websocketMessageType, dataMessage) -> str:
        return f"{self.websocketMessagePrefix}:{event}{self.websocketMessageSeparator}{websocketMessageType}{self.websocketMessageSeparator}{dataMessage}"

    def Emit(self, event: str, data=""):
        messageStr = self.encodeMessage(event, data)
        print(f"debug - {Bolors.OK}{messageStr}{Bolors.RESET}")
        self.send(messageStr)

    def f_open(self, ws: WebSocketApp):
        self.isReady = True
        self._open()

    def f_data(self, data, frameopcode, enabled):
        self._message(data)

    def f_err(self, err):
        pass

    def f_close(self, close_status_code: int, close_msg: str):
        self._close(close_msg, close_status_code)

    def _open(self):
        pass

    def _close(self, msg, code):
        pass

    def _message(self, message):
        pass


class Message:
    wait: str
    # The Namespace that this message sent to.
    Namespace: str
    # The Room that this message sent to.
    Room: str
    # The Event that this message sent to.
    Event: str
    # The actual body of the incoming data.
    Body: WSData
    """
     The Err contains any message's error if defined and not empty.
       server-side and client-side can return an error instead of a message from inside event callbacks. */
    """
    Err: str
    isError: bool
    isNoOp: bool

    isInvalid: bool
    """
     The IsForced if true then it means that this is not an incoming action but a force action.
       For example when websocket connection lost from remote the OnNamespaceDisconnect `Message.IsForced` will be true */
 
    """
    isForced: bool
    """
    The IsLocal reprots whether an event is sent by the client-side itself, i.e when `connect` call on `OnNamespaceConnect` event the `Message.IsLocal` will be true,
       server-side can force-connect a client to connect to a namespace as well in this case the `IsLocal` will be false.
    """
    isLocal: bool
    # The IsNative reports whether the Message is websocket native messages, only Body is filled.
    isNative: bool
    # The SetBinary can be filled to true if the client must send this message using the Binary format message.
    setBinary: bool

    @property
    def isConnect(self) -> bool:
        return True if self.Event == OnNamespaceConnect else False

    @property
    def isDisconnect(self) -> bool:
        return True if self.Event == OnNamespaceDisconnect else False

    @property
    def isRoomJoin(self) -> bool:
        return True if self.Event == OnRoomJoin else False

    @property
    def isRoomLeft(self) -> bool:
        return True if self.Event == OnRoomLeft else False

    @property
    def isWait(self) -> bool:
        if self.wait == "":
            return False
        if self.wait[0] == waitIsConfirmationPrefix:
            return True

        return True if self.wait[0] == waitComesFromClientPrefix else False

    def unmarshal(self) -> dict:
        return json.loads(self.Body)

    @property
    def isEmpty(self) -> bool:
        return self.wait is None or self.wait == ""

    @property
    def errIsEmpty(self) -> bool:
        return self.Err is None or self.Err == ""


"""
 marshal takes an object and returns its serialized to string form, equivalent to the Go's `neffos.Marshal`.
   It can be used on `emit` methods.   
   See `Message.unmarshal` method too.
"""


def marshal(obj: any) -> str:
    return json.dumps(obj)


messageSeparator = ";"
messageFieldSeparatorReplacement = "@%!semicolon@%!"
validMessageSepCount = 7
trueString = "1"
falseString = "0"


# escapeRegExp = new RegExp(messageSeparator, "g");
def escapeMessageField(s: str) -> str:
    if s == "":
        return ""
    text_after = re.sub(messageSeparator, messageFieldSeparatorReplacement, s)
    return text_after


def unescapeMessageField(s: str) -> str:
    if s == "":
        return ""
    text_after = re.sub(messageFieldSeparatorReplacement, messageSeparator, s)
    return text_after


def reply(body: WSData) -> replyError:
    return replyError(body)


# var messageSeparatorCharCode = messageSeparator.charCodeAt(0);
messageSeparatorCharCode = ord(messageSeparator[0])


def serializeMessage(msg: Message) -> Union[WSData, bytearray]:
    if msg.isNative and msg.isEmpty:
        return msg.Body
    isErrorString = falseString
    isNoOpString = falseString
    body = msg.Body if msg.Body else ""
    if msg.errIsEmpty is False:
        body = str(msg.Err)
        if isReplyErr(msg.Err) is False:
            isErrorString = trueString

    if msg.isNoOp is True:
        isNoOpString = trueString
    data = [
        msg.wait if msg.isEmpty is False else "",
        escapeMessageField(msg.Namespace),
        escapeMessageField(msg.Room),
        escapeMessageField(msg.Event),
        isErrorString,
        isNoOpString,
        ""
    ]
    data = messageSeparator.join(data)

    if msg.setBinary is True:
        """
        body is already in the form we need,
        
        let b = textEncoder.encode(data);
        data = new Uint8Array(b.length + body.length);
        data.set(b, 0);
        data.set(body, b.length);
        
        """
        encoded_string = data.encode()
        # https://www.kite.com/python/answers/how-to-convert-a-string-to-a-byte-array-in-python
        b = bytearray(encoded_string)
        print(len(b))
        data = b
    else:
        """
        If not specified to send as binary message,
        then don't send as binary.
         if (body instanceof Uint8Array) {
            body = textDecoder.decode(body, { stream: false });
        }
        data += body;
        """
        if isinstance(body, bytearray):
            body = body.decode()

        data += body

    return data


def splitN(s: str, sep: str, limit: int) -> list:
    """
    behaves like Go's SplitN, default javascript's does not return the remainder and we need this for the dts[6]

    :param s:
    :param sep:
    :param limit:
    :return:
    """
    if limit == 0:
        return [s]
    arr = s.split(sep, limit)
    if len(arr) == limit:
        curr = sep.join(arr) + sep
        arr.append(s[:len(curr)])
        return arr
    else:
        return [s]


"""
// <wait>;
// <namespace>;
// <room>;
// <event>;
// <isError(0-1)>;
// <isNoOp(0-1)>;
// <body||error_message>
"""


def deserializeMessage(data: any, allowNativeMessages: bool) -> Message:
    msg = Message()
    if len(data) == 0:
        msg.isInvalid = True
        return msg
    isArrayBuffer = isinstance(data, bytearray)
    dts: list = []
    if isArrayBuffer:
        arr = bytearray(data)
        sepCount = 1
        lastSepIndex = 0
        for i in range(len(arr)):
            if arr[i] == messageSeparatorCharCode:
                sepCount += 1
                lastSepIndex = i
                if sepCount == validMessageSepCount:
                    break

        if sepCount != validMessageSepCount:
            msg.isInvalid = True
            return msg
        dts = splitN(arr[0:lastSepIndex].decode(), messageSeparator, validMessageSepCount - 2)
        dts.append(data[lastSepIndex + 1, len(data)])
        msg.setBinary = True
    else:
        dts = splitN(data, messageSeparator, validMessageSepCount - 1)

    if len(dts) != validMessageSepCount:
        if not allowNativeMessages:
            msg.isInvalid = True
        else:
            msg.Event = OnNativeMessage
            msg.Body = data
        return msg
    msg.wait = dts[0]
    msg.Namespace = unescapeMessageField(dts[1])
    msg.Room = unescapeMessageField(dts[2])
    msg.Event = unescapeMessageField(dts[3])
    msg.isError = True if dts[4] == trueString else False
    msg.isNoOp = True if dts[5] == trueString else False

    body = dts[6]
    if body != "":
        if msg.isError:
            msg.Err = IOError(body)
        else:
            msg.Body = body
    else:
        """
        // if (isArrayBuffer) {
        //     msg.Body = new ArrayBuffer(0);
        // }
        
        """
        msg.Body = ""

    msg.isInvalid = False
    msg.isForced = False
    msg.isLocal = False
    msg.isNative = True if allowNativeMessages is True and msg.Event == OnNativeMessage else False
    return msg


def genWait() -> str:
    f = int(datetime.now().timestamp())
    return waitComesFromClientPrefix + str(f)


def genWaitConfirmation(wait: str) -> str:
    return waitIsConfirmationPrefix + wait


def genEmptyReplyToWait(wait: str) -> str:
    return wait + messageSeparator * (validMessageSepCount - 1)


"""
The Conn class contains the websocket connection and the neffos communication functionality.
   Its `connect` will return a new `NSConn` instance, each connection can connect to one or more namespaces.
   Each `NSConn` can join to multiple rooms.
"""


def dial(endpoint: str, connHandler: any, options=None) -> "Conn":
    return _dial(endpoint, connHandler, 0, options)


"""


function resolveNamespaces(obj: any, reject: (reason?: any) => void): Namespaces {
    if (isNull(obj)) {
        if (!isNull(reject)) {
            reject("connHandler is empty.");
        }
        return null;
    }

    let namespaces = new Map<string, Map<string, MessageHandlerFunc>>();

    // 1. if contains function instead of a string key then it's Events otherwise it's Namespaces.
    // 2. if contains a mix of functions and keys then ~put those functions to the namespaces[""]~ it is NOT valid.

    let events: Events = new Map<string, MessageHandlerFunc>();
    // const isMessageHandlerFunc = (value: any): value is MessageHandlerFunc => true;

    let totalKeys: number = 0;
    Object.keys(obj).forEach(function (key, index) {
        totalKeys++;
        let value = obj[key];
        // if (isMessageHandlerFunc(value)) {
        if (value instanceof Function) {
            // console.log(key + " event probably contains a message handler: ", value)
            events.set(key, value)
        } else if (value instanceof Map) {
            // console.log(key + " is a namespace map which contains the following events: ", value)
            namespaces.set(key, value);
        } else {
            // it's an object, convert it to a map, it's events.
            // console.log(key + " is an object of: ", value);
            let objEvents = new Map<string, MessageHandlerFunc>();
            Object.keys(value).forEach(function (objKey, objIndex) {
                // console.log("set event: " + objKey + " of value: ", value[objKey])
                objEvents.set(objKey, value[objKey]);
            });
            namespaces.set(key, objEvents)
        }
    });

    if (events.size > 0) {
        if (totalKeys != events.size) {
            if (!isNull(reject)) {
                reject("all keys of connHandler should be events, mix of namespaces and event callbacks is not supported " + events.size + " vs total " + totalKeys);
            }
            return null;
        }
        namespaces.set("", events);
    }

    // console.log(namespaces);
    return namespaces;
}

"""


def _dial() -> "Conn":
    pass


# to be continued.
def resolveNamespaces(handlers: any) -> Namespaces:
    pass


class Conn:
    """
    ID is the generated connection ID from the server-side, all connected namespaces(`NSConn` instances)
      that belong to that connection have the same ID. It is available immediately after the `dial`.
    """
    ID: str

    """
     If > 0 then this connection is the result of a reconnection,
       see `wasReconnected()` too. 
    """
    conn: NeffSupportSocket
    reconnectTries: int
    _isAcknowledged: bool
    _allowNativeMessages: bool
    _closed: bool
    _queue: list
    # Map<string, waitingMessageFunc>;
    _waitingMessages: dict
    # Events = Map<string, MessageHandlerFunc>;
    #  Map<string, Events>;
    namespaces: Namespaces
    #  Map<string, NSConn>
    connectedNamespaces: dict
    #  Map<string, () => void>;
    _waitServerConnectNotifiers: dict

    def __init__(self, conn: NeffSupportSocket, namespaces: Namespaces):
        self.conn = conn
        self.reconnectTries = 0
        self._isAcknowledged = False
        self.namespaces = namespaces

        hasEmptyNS = namespaces.get("", False)
        self._allowNativeMessages = hasEmptyNS and namespaces.get("") == OnNativeMessage
        self._queue = list()
        self._waitingMessages = dict()
        self.connectedNamespaces = dict()
        self._closed = False

    def wasReconnected(self) -> bool:
        return self.reconnectTries > 0

    def isAcknowledged(self) -> bool:
        return self._isAcknowledged

    def handle(self, evt: MesssageEvent) -> Union[IOError, None]:
        if not self._isAcknowledged:
            err = self.handleAck(evt.data)
            if err is None:
                self._isAcknowledged = True
                self.handleQueue()
            else:
                self.conn.close()
            return err
        return self.handleMessage(evt.data)

    def handleAck(self, data: WSData) -> Union[IOError, None]:
        typ = data[0]

        if typ == ackBinary:
            idf = data[1:]
            self.ID = idf

        elif typ == ackNotOKBinary:
            errorText = data[1:]
            return IOError(errorText)
        else:
            self._queue.append(data)
            return None

    def handleQueue(self):
        if self._queue is None or len(self._queue) == 0:
            return
        for index in range(len(self._queue)):
            value = self._queue[index]

    def handleMessage(self, data: WSData) -> Union[IOError, None]:
        msg = deserializeMessage(data, self._allowNativeMessages)
        if msg.isInvalid:
            return ErrInvalidPayload()
        if msg.isInvalid and self._allowNativeMessages:
            ns = self.handleNamespace("")
            return fireEvent(ns, msg)
        if msg.isWait:
            cb = self._waitingMessages.get(msg.wait)
            cb(msg)
            return None
        ns = self.handleNamespace(msg.Namespace)
        if msg.Event == OnNamespaceConnect:
            self.replyConnect(msg)
        elif msg.Event == OnNamespaceDisconnect:
            self.replyDisconnect(msg)
        elif msg.Event == OnRoomJoin:
            if ns is not None:
                ns.replyRoomJoin(msg)
        elif msg.Event == OnRoomLeave:
            if ns is not None:
                ns.replyRooomLeave(msg)
        else:
            if ns is None:
                return ErrBadNamespace()
            msg.isLocal = False
            err = fireEvent(ns, msg)
            if err is not None:
                msg.Err = err
                self.write(msg)
                return err
        return None

    def connect(self, namespace: str) -> NSConn:
        return self.askConnect(namespace)

    def waitServerConnect(self, namespace: str) -> NSConn:
        if self._waitServerConnectNotifiers is None:
            self._waitServerConnectNotifiers = dict()
        self._waitServerConnectNotifiers.setdefault(namespace, lambda: self._waitServerConnectNotifiers.pop(namespace, None))
        return self.handleNamespace(namespace)

    def replyConnect(self, msg: Message) -> None:
        if msg.isEmpty or msg.isNoOp:
            return
        ns = self.handleNamespace(msg.Namespace)
        if ns is not None:
            self.writeEmptyReply(msg.wait)
            return
        events = getEvents(self.namespaces, msg.Namespace)
        if events is None:
            msg.Err = ErrBadNamespace
            self.write(msg)
            return
        ns = NSConn(self, msg.Namespace, events)
        self.connectedNamespaces.setdefault(msg.Namespace, ns)
        self.writeEmptyReply(msg.wait)
        msg.Event = OnNamespaceConnected
        fireEvent(ns, msg)
        if self._waitServerConnectNotifiers is not None and len(self._waitServerConnectNotifiers) > 0:
            if self._waitServerConnectNotifiers.__contains__(msg.Namespace):
                self._waitServerConnectNotifiers.get(msg.Namespace)()

    def replyDisconnect(self, msg: Message) -> None:
        if msg.isEmpty or msg.isNoOp:
            return
        ns = self.handleNamespace(msg.Namespace)
        if ns is not None:
            self.writeEmptyReply(msg.wait)
            return
        ns.forceLeaveAll(True)
        self.connectedNamespaces.pop(msg.Namespace, None)
        self.writeEmptyReply(msg.wait)
        fireEvent(ns, msg)

    def isClosed(self) -> bool:
        return self._closed

    def ask(self, msg: Message) -> Union[Message, IOError]:
        if self.isClosed():
            return ErrClosed()
        msg.wait = genWait()
        self._waitingMessages.setdefault(msg.wait, lambda r: await self.handle_receive(r))
        if self.write(msg) is False:
            return ErrClosed()

    async def handle_receive(self, rec: Message) -> None:
        if rec.isError:
            raise ErrClosed()

    def writeEmptyReply(self, wait: str) -> None:
        self.conn.send(genEmptyReplyToWait(wait))

    def askConnect(self, namespace: str) -> Union[NSConn, IOError]:
        ns = self.handleNamespace(namespace)
        if ns is not None:
            return ns

        events = getEvents(self.namespaces, namespace)
        if events is None:
            raise ErrBadNamespace()

        connectmessage = Message()
        connectmessage.Namespace = namespace
        connectmessage.Event = OnNamespaceConnected
        connectmessage.isLocal = True
        ns = NSConn(self, namespace, events)
        err = fireEvent(ns, connectmessage)
        if err is not None:
            raise err

        try:
            self.ask(connectmessage)
        except IOError as e:
            raise e
        self.connectedNamespaces.setdefault(namespace, ns)

        fireEvent(ns, connectmessage)

        return ns

    def askDisconnect(self, msg: Message):
        ns = self.handleNamespace(msg.Namespace)
        if ns is None:
            raise ErrBadNamespace()
        try:
            self.ask(msg)
        except IOError as e:
            raise e
        ns.forceLeaveAll(True)

        self.connectedNamespaces.pop(msg.Namespace, None)
        msg.isLocal = True
        return fireEvent(ns, msg)

    def handleNamespace(self, ns: str) -> NSConn:
        """
             The namespace method returns an already connected `NSConn`
            :param ns: the namespace
            :return: NSConn
        """
        return self.connectedNamespaces.get(ns)

    def write(self, msg: Message) -> bool:
        if self.isClosed():
            return False
        if msg.isConnect is False and msg.isDisconnect is False:
            ns = self.handleNamespace(msg.Namespace)
            if ns is None:
                return False
            if msg.Room != "" and msg.isRoomJoin is False and msg.isRoomLeft is False:
                # tried to send to a not joined room.
                # if (!ns.rooms.has(msg.Room)) {
                return False
                # }

        self.conn.send(serializeMessage(msg))
        return True

    def writeEmptyReply(self, wait: str):
        self.conn.send(genEmptyReplyToWait(wait))

    def close(self):
        if self.isClosed():
            return

        disconnectMsg = Message()
        disconnectMsg.Event = OnNamespaceDisconnect
        disconnectMsg.isForced = True
        disconnectMsg.isLocal = True
        for ns in self.connectedNamespaces:
            ns.forceLeaveAll(True)
            disconnectMsg.Namespace = ns
            fireEvent(ns, disconnectMsg)
            self.connectedNamespaces.pop(ns, None)
        self._waitingMessages.clear()
        self._closed = True

        if self.conn.readyState == self.conn.OPEN:
            self.conn.close()


"""
class NSConn {
  /* The conn property refers to the main `Conn` constructed by the `dial` function. */
  conn: Conn;
  namespace: string;
  events: Events;
  /* The rooms property its the map of the connected namespace's joined rooms. */
  rooms: Map<string, Room>;
  constructor(conn: Conn, namespace: string, events: Events);
  /* The emit method sends a message to the server with its `Message.Namespace` filled to this specific namespace. */
  emit(event: string, body: WSData): boolean;
  /* See `Conn.ask`. */
  ask(event: string, body: WSData): Promise<Message>;
  /* The joinRoom method can be used to join to a specific room, rooms are dynamic.
     Returns a `Room` or an error. */
  joinRoom(roomName: string): Promise<Room>;
  /* The room method returns a joined `Room`. */
  room(roomName: string): Room;
  /* The leaveAll method sends a leave room signal to all rooms and fires the `OnRoomLeave` and `OnRoomLeft` (if no error occurred) events. */
  leaveAll(): Promise<Error>;
  /* The disconnect method sends a disconnect signal to the server and fires the `OnNamespaceDisconnect` event. */
  disconnect(): Promise<Error>;
}


"""


class NSConn:
    """
    The NSConn describes a connected connection to a specific namespace,
   it emits with the `Message.Namespace` filled and it can join to multiple rooms.
   A single Conn can be connected to one or more namespaces,
   each connected namespace is described by this class.
    """
    conn: Conn
    namespace: str
    events: dict
    #  The rooms property its the map of the connected namespace's joined rooms.
    # Map<string, Room>;
    rooms: dict

    def __init__(self, conn: Conn, namespace: str, events: Events):
        self.conn = conn
        self.namespace = namespace
        self.events = events
        self.rooms = dict()

    def emit(self, event: str, body: WSData) -> bool:
        msg = Message()
        msg.Namespace = self.namespace
        msg.Event = event
        msg.Body = body
        return self.conn.write(msg)

    def emitBinary(self, event: str, body: WSData) -> bool:
        """
        The emitBinary method sends a binary message to the server with its `Message.Namespace` filled to this specific namespace
       and `Message.SetBinary` to true.
        :param event:
        :param body:
        :return:
        """
        msg = Message()
        msg.Namespace = self.namespace
        msg.Event = event
        msg.Body = body
        msg.setBinary = True
        return self.conn.write(msg)

    def ask(self, event: str, body: WSData) -> Message:
        msg = Message()
        msg.Namespace = self.namespace
        msg.Event = event
        msg.Body = body
        return self.conn.ask(msg)

    def joinRoom(self, roomName: str) -> "Room":
        return self.askRoomJoin(roomName)

    def room(self, roomName: str) -> "Room":
        """
         The room method returns a joined `Room`.
        :param roomName:
        :return:
        """
        return self.rooms.get(roomName)

    def leaveAll(self) -> Union[IOError, None]:
        msg = Message()
        msg.Namespace = self.namespace
        msg.Event = OnRoomLeft
        msg.isLocal = True
        for v in self.rooms:
            roomName = self.rooms[v].name
            msg.Room = roomName
            err = self.askRoomLeave(msg)
            if err is not None:
                return err
        return None

    def forceLeaveAll(self, isLocal: bool):
        leaveMsg = Message()
        leaveMsg.Namespace = self.namespace
        leaveMsg.Event = OnRoomLeave
        leaveMsg.isForced = True
        leaveMsg.isLocal = isLocal
        for v in self.rooms:
            roomName = self.rooms[v].name
            leaveMsg.Room = roomName
            fireEvent(self, leaveMsg)
            self.rooms.pop(roomName)
            leaveMsg.Event = OnRoomLeft
            fireEvent(self, leaveMsg)
            leaveMsg.Event = OnRoomLeave

    def disconnect(self):
        """
        The disconnect method sends a disconnect signal to the server and fires the `OnNamespaceDisconnect` event.
        :return:
        """
        disconnectMsg = Message()
        disconnectMsg.Namespace = self.namespace
        disconnectMsg.Event = OnNamespaceDisconnect
        return self.conn.askDisconnect(disconnectMsg)

    # async
    def askRoomJoin(self, roomname: str) -> Union["Room", None]:
        room = self.rooms.get(roomname)
        if room is not None:
            return room

        joinMsg = Message()
        joinMsg.Namespace = self.namespace
        joinMsg.Room = roomname
        joinMsg.Event = OnRoomJoin
        joinMsg.isLocal = True
        try:
            self.conn.ask(joinMsg)
        except IOError as e:
            print(e)
            return None
        err = fireEvent(self, joinMsg)
        if err is not None:
            return err
        room = Room(self, roomname)
        self.rooms.setdefault(roomname, room)
        joinMsg.Event = OnRoomJoined

        fireEvent(self, joinMsg)

        return room

    # async
    def askRoomLeave(self, msg: Message) -> Union[IOError, None]:
        if self.rooms.__contains__(msg.Room) is False:
            return ErrBadRoom()
        try:
            self.conn.ask(msg)
        except IOError as e:
            return e
        err = fireEvent(self, msg)
        if err is not None:
            return err
        self.rooms.__delitem__(msg.Room)
        msg.Event = OnRoomLeave

        fireEvent(self, msg)

        return None

    # async
    def replyRoomJoin(self, msg: Message) -> None:
        if msg.isEmpty or msg.isNoOp:
            return

    def replyRoomLeave(self, msg: Message) -> None:
        if msg.isEmpty or msg.isNoOp:
            return


def fireEvent(ns: NSConn, msg: Message) -> Union[IOError, None]:
    if ns.events.__contains__(msg.Event):
        return ns.events.get(msg.Event)(ns, msg)
    if ns.events.__contains__(OnAnyEvent):
        return ns.events.get(OnAnyEvent)(ns, msg)
    return None


class Room:
    """
     The Room describes a connected connection to a room,
   emits messages with the `Message.Room` filled to the specific room
   and `Message.Namespace` to the underline `NSConn`'s namespace.
    """
    nsConn: NSConn
    name: str

    def __init__(self, ns: NSConn, roomName: str):
        self.nsConn = ns
        self.name = roomName

    def emit(self, event: str, body: WSData) -> bool:
        msg = Message()
        msg.Namespace = self.nsConn.namespace
        msg.Room = self.name
        msg.Event = event
        msg.Body = body
        return self.nsConn.conn.write(msg)

    def leave(self) -> None:
        msg = Message()
        msg.Namespace = self.nsConn.namespace
        msg.Room = self.name
        msg.Event = OnRoomLeave
        return self.nsConn.askRoomLeave(msg)
