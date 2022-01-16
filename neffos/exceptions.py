class ErrInvalidPayload(IOError):
    pass


class ErrBadNamespace(IOError):
    pass


class ErrBadRoom(IOError):
    pass


class ErrClosed(IOError):
    pass


class ErrWrite(IOError):
    pass


class replyError(IOError):
    """
    Maybe need to add more stacktrace for this error
    Error.captureStackTrace(this, replyError);
    Object.setPrototypeOf(this, replyError.prototype);
    in JS version
    """

    def __init__(self, message: str):
        super().__init__(message)
        self.name = "replyError"


def isReplyErr(err: any) -> bool:
    return isinstance(err, replyError)


def isCloseError(err: IOError) -> bool:
    """
    if (err && !isEmpty(err.message)) {
        return err.message.indexOf("[-1] write closed") >= 0;
    }
    """
    # if err is True and
    return False
