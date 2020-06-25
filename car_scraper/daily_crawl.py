import os
import time
import datetime
import psutil
import subprocess

base_dir = os.path.dirname(os.path.abspath(__file__))

start_time = '07:10'
detail_flag_runtime = True
link_flag_runtime = True

#################### For Detail Scraper ########################
def detail_valid_runtime(start_hour, start_min, current_hr, current_min):
    try:
        max_hour = start_hour
        max_min = start_min + 2
        if max_min >= 60:
            max_hour += 1
            if max_hour >= 24:
                max_hour = max_hour - 24
            max_min = max_min - 60

        maxTime = datetime.time(max_hour, max_min)
        startTime = datetime.time(start_hour, start_min)
        currentTime = datetime.time(current_hr, current_min)
        
        if maxTime > currentTime >= startTime:
            return True
        return False
    except:
        return False

def detail_valid_killtime(start_hour, start_min, current_hr, current_min):
    try:
        min_hour = start_hour
        min_min = start_min - 2
        if min_min < 0:
            min_hour -= 1
            if min_hour < 0:
                min_hour = min_hour + 24
            min_min = min_min + 60

        minTime = datetime.time(min_hour, min_min)
        startTime = datetime.time(start_hour, start_min)
        currentTime = datetime.time(current_hr, current_min)

        if startTime > currentTime >= minTime:
            return True
        return False
    except:
        return False

def detail_kill_subprocess():
    try:
        PROCNAME = "python"
        for proc in psutil.process_iter():
            if proc.name() == PROCNAME:
                if proc.cmdline() == ['python', base_dir + '/details.py']:
                    proc.kill()
    except :
        return

#################### For Link Scraper ########################
def link_valid_runtime(start_hour, start_min, current_hr, current_min):
    try:
        max_hour = start_hour
        max_min = start_min + 5
        if max_min >= 60:
            max_hour += 1
            if max_hour >= 24:
                max_hour = max_hour - 24
            max_min = max_min - 60

        maxTime = datetime.time(max_hour, max_min)
        startTime = datetime.time(start_hour, start_min)
        currentTime = datetime.time(current_hr, current_min)
        
        if maxTime > currentTime >= startTime:
            return True
        return False
    except:
        return False

def link_valid_killtime(start_hour, start_min, current_hr, current_min):
    try:
        min_hour = start_hour
        min_min = start_min - 5
        if min_min < 0:
            min_hour -= 1
            if min_hour < 0:
                min_hour = min_hour + 24
            min_min = min_min + 60

        minTime = datetime.time(min_hour, min_min)
        startTime = datetime.time(start_hour, start_min)
        currentTime = datetime.time(current_hr, current_min)

        if startTime > currentTime >= minTime:
            return True
        return False
    except:
        return False

def link_kill_subprocess():
    try:
        PROCNAME = "python"
        for proc in psutil.process_iter():
            if proc.name() == PROCNAME:
                if proc.cmdline() == ['python', base_dir + '/links.py']:
                    proc.kill()
    except :
        return

####################### Main Function #########################
def main():
    global start_time, detail_flag_runtime, link_flag_runtime

    while True:
        # try:
        # current time
        currentDT = datetime.datetime.now()
        currentHr = currentDT.hour
        currentMin = currentDT.minute
        
        # detail start time
        detail_startHr = int(start_time.split(':')[0].strip())
        detail_startMin = int(start_time.split(':')[1].strip())

        # link start time
        link_startHr = detail_startHr
        link_startMin = detail_startMin + 10

        if link_startMin >= 60:
            link_startHr += 1
            if link_startHr >= 24:
                link_startHr = link_startHr - 24
            link_startMin = link_startMin - 60

        if detail_valid_runtime(detail_startHr, detail_startMin, currentHr, currentMin) and not detail_flag_runtime:
            detail_flag_runtime = True
            print('--------------------------------')
            print('starting details.py process.......')
            time.sleep(10)

            output = subprocess.Popen("python " + base_dir + "/details.py", shell=True, universal_newlines=True)

        if detail_valid_killtime(detail_startHr, detail_startMin, currentHr, currentMin) and detail_flag_runtime:
            
            crawling_status = False

            # killing process
            detail_kill_subprocess()

            print('--------------------------------')
            print('killing details.py process.......')
            time.sleep(5)

            print('Prepairing Start details.py Process.......')
            time.sleep(5)
            detail_flag_runtime = False

        if link_valid_runtime(link_startHr, link_startMin, currentHr, currentMin) and not link_flag_runtime:
            link_flag_runtime = True
            print('--------------------------------')
            print('starting links.py process.......')
            time.sleep(10)

            output = subprocess.Popen("python " + base_dir + "/links.py", shell=True, universal_newlines=True)

        if link_valid_killtime(link_startHr, link_startMin, currentHr, currentMin) and link_flag_runtime:
            
            crawling_status = False

            # killing process
            link_kill_subprocess()

            print('--------------------------------')
            print('links.py killing process.......')
            time.sleep(5)

            print('Prepairing Start links.py Process.......')
            time.sleep(5)
            link_flag_runtime = False
            
        # except:

        #     continue
        time.sleep(60)

if __name__ == "__main__":
    main()