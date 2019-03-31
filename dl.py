#!/usr/bin/python3
# General Downloader
#
#

import better_exceptions
import urllib.request
import argparse
import time
import queue
import threading
import os,sys
#
def download():
    global broken_links, internal_error, failed, ls
    while not qq.empty():
        mydata = threading.local()
        mydata.name, mydata.url = qq.get()
        if mydata.name in ls:continue
        try:
            mydata.html = urllib.request.urlopen(mydata.url)
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

def mkqueue_album_gen():
    fhand = open(args.fname,'r')
    links = []
    i , j = (args.FROM,1)
    for each in fhand:
        if each.startswith(args.identify):
            i = i + 1
            j = 1
        if each.startswith('#') or len(each) < 10:continue
        if not args.ORIGINAL_NAME:
            fname = "R"+str(i)+ "_" + str(j).zfill(4) + "." + each.strip().split('.')[-1]
        else:
            fname = "R"+str(i)+ "_" + each.strip().split('/')[-1]
        links.append((fname,each.strip()))
        j = j + 1
    for each in links:qq.put(each)
    fhand.close()

def mkqueue_no_album():
    fhand = open(args.fname,'r')
    i = 1
    for each in fhand:
        if each.startswith('#') or len(each) < 10:continue
        if not args.ORIGINAL_NAME:
            qq.put((args.prefix+str(i).zfill(5) + "." + each.strip().split('.')[-1], each.strip()))
            #qq.put((args.prefix+str(1000 + i) + "." + each.strip().split('.')[-1], each.strip()))
            i = i + 1
        else:qq.put(each.strip().split('')[-1], each.strip())
    fhand.close()

def mkqueue_get_album():
    ref = dict()
    fhand = open(args.fname,'r')
    for each in fhand:
        if each.startswith(args.identify):
            i = each.split('album=')[-1].strip().zfill(4)
            if i not in ref.keys():ref[i] = 1001
        if each.startswith('#') or len(each) < 10:continue
        if args.ORIGINAL_NAME:
            fname = i+ "_" + each.strip().split('/')[-1]
        else:
            fname = i+ "_" + str(ref[i]) + "." + each.strip().split('.')[-1]
        qq.put((fname,each.strip()))
        ref[i] = ref[i] + 1
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
parser.add_argument('-o', dest='ORIGINAL_NAME', action='store_true', required = False,
                    help='Use the original file names')
parser.add_argument('-s', dest='SINGLE_ALBUM', action='store_true', required = False,
                    help='Invoke Single Album Mode')
parser.add_argument('--preix', dest='prefix', type = str, default = "R", required = False,
                    help='Prefix to file names  [Used with single album mode]')
parser.add_argument('-g', dest='GENERATE_ALBUM_NO', action='store_true', required = False,
                    help='Invoke Auto-Generation of Album No')
parser.add_argument('--from', dest='FROM', type = int, default = 100, required = False,
                    help='Start Album no from here [Used with auto generation of album no]')
args = parser.parse_args()

#
qq = queue.Queue()
started = time.time()
threads = []
links   = []
failed  = []
broken_links    = 00
internal_error  = 00
ls = os.listdir(os.getcwd())

if args.GENERATE_ALBUM_NO:mkqueue_album_gen()
elif args.SINGLE_ALBUM:mkqueue_no_album()
else:mkqueue_get_album()
files = os.listdir(os.getcwd())
total = qq.qsize()
print(str(total),"Files queued for download.")

#while not qq.empty():
#    name, url = qq.get()
#    print(name,url)
#quit()
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


print(" \n ============================ \n    Time Taken : {} \n Files Downloaded : {} \n    Failed Downloads\
    : {} \n    Broken Links : {}  \n ===============================================================".format(\
    time.strftime("%H:%M:%S",time.gmtime(time.time()-started)), total-len(failed),len(failed),broken_links))
print(args.SINGLE_ALBUM)
#
