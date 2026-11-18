import os,signal,sys,time,traceback
mode=sys.argv[1]
print(f'CHILD_PID={os.getpid()} MODE={mode}',flush=True)
if mode=='normal':print('normal stdout',flush=True)
elif mode=='early':
 print('early stderr',file=sys.stderr,flush=True)
 try:raise RuntimeError('synthetic early failure')
 except RuntimeError:traceback.print_exc(file=sys.stderr)
 sys.exit(7)
elif mode=='timeout':
 signal.signal(signal.SIGTERM,signal.SIG_IGN)
 print('timeout ready',flush=True)
 while True:time.sleep(0.1)
elif mode=='cancel':
 signal.signal(signal.SIGTERM,signal.SIG_IGN)
 print('cancel ready',flush=True)
 while True:time.sleep(0.1)
elif mode=='tmpdir':
 import tempfile
 print('TMPDIR='+tempfile.gettempdir(),flush=True)
 p=tempfile.NamedTemporaryFile(delete=False);p.write(b'synthetic');p.close()
 print('TMPFILE='+p.name,flush=True)
elif mode=='outside':
 target=sys.argv[2]
 print('OUTSIDE_EXISTS='+str(os.path.exists(target)),flush=True)
 try:open(target).read();sys.exit(9)
 except FileNotFoundError:sys.exit(0)
else:sys.exit(10)
