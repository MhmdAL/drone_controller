import olympe

LOG_FILE_BASE = './log'

log_file = LOG_FILE_BASE

def init_logger(station_id):
    global log_file; log_file = LOG_FILE_BASE + station_id

def log(message):
    file_object = open(log_file, 'a')

    file_object.write(message + '\n')
        
    file_object.close()

def log_event(event):
    if isinstance(event, olympe.ArsdkMessageEvent):
        max_args_size = 100
        args = str(event.args)
        args = (args[: max_args_size - 3] + "...") if len(args) > max_args_size else args
        
        log("{}({})\n".format(event.message.fullName, args))
    else:
        print(str(event))
