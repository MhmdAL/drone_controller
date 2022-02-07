LOG_FILE_BASE = '/app/log'

log_file = LOG_FILE_BASE

def init_logger(station_id):
    global log_file; log_file = LOG_FILE_BASE + station_id

def log(message):
    file_object = open(log_file, 'a')

    file_object.write(message + '\n')
        
    file_object.close()