#!/usr/bin/python3
# General Downloader
#
#

import urllib.request
import argparse
import time
import queue
import threading
import os,sys
#
def download():
    global broken_links, internal_error, failed
    while not qq.empty():
        mydata = threading.local()
        mydata.name, mydata.url = qq.get()
        if mydata.name in files:continue
        try:
            mydata.html = urllib.request.urlopen(mydata.url,timeout=25)
        except urllib.error.HTTPError as HERR:
            if HERR.code == 404:broken_links += 1
            if HERR.code == 500:internal_error +=1
            continue
        except:
            for tmp in range(2):
                try:
                    mydata.html = urllib.request.urlopen(mydata.url)
                    if mydata.html.getcode() == 200:break
                except:continue
            print("\n ERROR : GET ERROR :",mydata.name,mydata.url)
            failed.append((mydata.name,mydata.url))
            continue
        try:mydata.image = mydata.html.read()
        except:
            print("\n ERROR : READ ERROR :",mydata.name,mydata.url)
            failed.append((mydata.name,mydata.url))
            continue
        try:open(mydata.name,'wb').write(mydata.image)
        except:
            print("\n ERROR : WRITE ERROR :",mydata.name,mydata.url)
            failed.append((mydata.name,mydata.url))
            continue
#        print("INFO : Downloaded",mydata.name)

def mkqueue():
    fhand = open(args.fname,'r')
    links = []
    i , j = (args.last,101)
    for each in fhand:
        if each.startswith(args.identify):
            i = i + 1
            j = 101
        if each.startswith('#') or len(each) < 10:continue
        fname = str(i)+ "_" + str(j) + "." + each.strip().split('.')[-1]
        links.append((fname,each.strip()))
        j = j + 1
    for each in links:qq.put(each)
    fhand.close()

def enqueue():
    if qq.qsize() != 0:print("\n WARNING: Queue was not empty. ")
    for name,url in failed:
        qq.put((name,url))

def init_threads():
    for i in range(args.threads):
        t = threading.Thread(target=download)
        threads.append(t)
        t.start()

def update_progress():
    progress = 100 - int((100*qq.qsize()) / total)
    te = time.strftime("%H:%M:%S",time.gmtime(time.time()-started))
    pbar = "\r {:0>3}% [{:<50}] ({},{}) Time Elapsed : {} ".format(progress, '#'*int((progress/2)), (total-qq.qsize()), total, te)
    sys.stdout.write(pbar)
    sys.stdout.flush()

#

parser = argparse.ArgumentParser(description='Start Tao Downloader.')
parser.add_argument('fname', type=str,
                    help='The File containing list of links.')
parser.add_argument('--dir', dest='directory', type = str, default = None, required = False,
                    help='The directory to download files in.')
parser.add_argument('--threads', dest='threads', type = int, default = 4, required = False,
                    help='No. of threads to use.')
parser.add_argument('--identify', dest='identify', type = str, default = "#!!!", required = False,
                    help='Identifier that seperate group of links belonging to different albums.')
parser.add_argument('--last', dest='last', type = int, default = 1000, required = False,
                    help='No. of last album.')
parser.add_argument('-f', dest='failed', action='store_true', required = False,
                    help='If restarting failed download.')
args = parser.parse_args()

#
qq = queue.Queue()
started = time.time()
threads = []
links   = []
failed  = []
broken_links    = 00
internal_error  = 00

if args.failed:
    for each in open(args.fname,'r'):
        if not each.startswith('#') and len(each.strip().split('=')) == 2:
            qq.put((each.strip().split('=')[0],each.strip().split('=')[1]))
else:mkqueue()
files = os.listdir(os.getcwd())
total = qq.qsize()
print(str(total),"Files queued for download.")

if args.directory is not None:
    if not os.path.exists(args.directory):os.makedirs(args.directory)
    os.chdir(args.directory)

init_threads()
while not qq.empty():
    update_progress()
    time.sleep(5)
for t in threads:t.join()

if len(failed) > 0:
    print("\n INFO : Download failed for {} Items. Trying Again ...".format(len(failed)))
    enqueue()
    failed.clear()
    init_threads()
    for t in threads:t.join()
    print("\n INFO:",len(failed),"Downloads Failed.")

if len(failed) > 0:
    print("\n INFO : Download failed for {} Items. Writing to file ...".format(len(failed)))
    fhand = open("Failed",'w')
    for name,url in failed:
        fhand.write(name+"="+url+"\n")
    fhand.close()

print(" \n ============================ \n    Time Taken : {} \n Files Downloaded : {} \n    Failed Downloads\
    : {} \n    Broken Links : {}  \n ===============================================================".format(\
    time.strftime("%H:%M:%S",time.gmtime(time.time()-started)), total-len(failed),len(failed),broken_links))

#
