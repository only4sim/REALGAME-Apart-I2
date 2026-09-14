"""Inspect tagged text in the exact supplied Word PDF using only the standard library.

This restricted audit helper is not a general PDF parser or a renderer. It rejects
other input bytes. It never reads credentials, follows links, or executes PDF data.
"""
import re,zlib,json,hashlib,argparse
from pathlib import Path

class Parser:
 def __init__(self,b): self.b=b;self.i=0
 def space(self):
  while self.i<len(self.b):
   if self.b[self.i] in b' \t\r\n\x00\x0c': self.i+=1
   elif self.b[self.i]==37:
    while self.i<len(self.b) and self.b[self.i] not in b'\r\n':self.i+=1
   else:break
 def val(self):
  self.space();b=self.b;i=self.i
  if i>=len(b):raise EOFError
  if b[i:i+2]==b'<<':
   self.i+=2;d={}
   while True:
    self.space()
    if b[self.i:self.i+2]==b'>>':self.i+=2;return d
    k=self.val();d[k]=self.val()
  c=b[i];self.i+=1
  if c==91:
   a=[]
   while True:
    self.space()
    if b[self.i]==93:self.i+=1;return a
    a.append(self.val())
  if c==47:
   m=re.match(rb'[^\s<>\[\]()/%%]+',b[self.i:]);s=m[0];self.i+=len(s)
   return '/'+re.sub(rb'#([0-9A-Fa-f]{2})',lambda m:bytes([int(m[1],16)]),s).decode('latin1')
  if c==40:
   out=bytearray();level=1
   while level:
    c=b[self.i];self.i+=1
    if c==92:
     c=b[self.i];self.i+=1
     if c in b'nrtbf':out.extend({110:b'\n',114:b'\r',116:b'\t',98:b'\b',102:b'\f'}[c])
     elif c in b'\r\n':
      if c==13 and b[self.i:self.i+1]==b'\n':self.i+=1
     elif c in b'01234567':
      s=bytes([c])
      while len(s)<3 and b[self.i:self.i+1] in [bytes([n]) for n in b'01234567']:
       s+=b[self.i:self.i+1];self.i+=1
      out.append(int(s,8))
     else:out.append(c)
    elif c==40:level+=1;out.append(c)
    elif c==41:
     level-=1
     if level:out.append(c)
    else:out.append(c)
   return bytes(out)
  if c==60:
   end=b.index(b'>',self.i);s=re.sub(rb'\s',b'',b[self.i:end]);self.i=end+1
   return bytes.fromhex((s+b'0' if len(s)%2 else s).decode())
  self.i=i;m=re.match(rb'[^\s<>\[\]()/%%]+',b[i:])
  if not m:raise ValueError((i,b[i:i+50]))
  s=m[0];self.i+=len(s)
  if re.fullmatch(rb'[+-]?(\d+\.?\d*|\.\d+)',s):
   v=float(s) if b'.' in s else int(s)
   if type(v) is int:
    ref=re.match(rb'\s+(\d+)\s+R\b',b[self.i:])
    if ref:self.i+=len(ref[0]);return ('ref',v,int(ref[1]))
   return v
  return s.decode('latin1')

class PDF:
 def __init__(self,path):
  self.raw=Path(path).read_bytes()
  if hashlib.sha256(self.raw).hexdigest()!='355c6c35f4723f202d2bb9fefb9ef8847bce810e7b8724d74e8aa3ea3f57a2f8':raise ValueError('This audit helper supports only the inventoried supplied paper PDF')
  self.rawobjs={int(m[1]):m[2] for m in re.finditer(rb'(\d+) 0 obj\s*(.*?)endobj',self.raw,re.S)}
  for n,b in list(self.rawobjs.items()):
   if b'/Type/ObjStm' in b:
    p=Parser(b).val();data=self.stream(n);first=p['/First'];inds=list(map(int,data[:first].split()))
    for i in range(0,len(inds),2):self.rawobjs[inds[i]]=data[first+inds[i+1]:first+inds[i+3] if i+3<len(inds) else len(data)]
  self.objects={k:Parser(v).val() for k,v in self.rawobjs.items()};self.fonts={};self.mcids={};self.runs={}
  for n,v in self.objects.items():
   if not isinstance(v,dict) or v.get('/Type')!='/Font':continue
   if '/ToUnicode' not in v:self.fonts[n]=None;continue
   cm=self.stream(v['/ToUnicode'][1]);mapping={}
   for batch in re.findall(rb'beginbfchar(.*?)endbfchar',cm,re.S):
    for x,y in re.findall(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>',batch):mapping[int(x,16)]=bytes.fromhex(y.decode()).decode('utf-16-be')
   for batch in re.findall(rb'beginbfrange(.*?)endbfrange',cm,re.S):
    for line in batch.splitlines():
     ps=Parser(line)
     try:start=ps.val();end=ps.val();target=ps.val()
     except EOFError:continue
     a=int.from_bytes(start,'big');b=int.from_bytes(end,'big')
     for offset,code in enumerate(range(a,b+1)):
      v=target[offset] if isinstance(target,list) else (int.from_bytes(target,'big')+offset).to_bytes(len(target),'big')
      mapping[code]=v.decode('utf-16-be')
   self.fonts[n]=mapping
  self.pageids=self.objects[2]['/Kids'];self.pages={x[1]:i+1 for i,x in enumerate(self.pageids)}
  for ref in self.pageids:self.readpage(ref[1])
 def deref(self,x):return self.objects[x[1]] if isinstance(x,tuple) else x
 def stream(self,n):
  b=self.rawobjs[n];p=Parser(b);d=p.val();m=re.match(rb'\s*stream\r?\n',b[p.i:]);start=p.i+len(m[0]);raw=b[start:start+d['/Length']]
  return zlib.decompress(raw) if d.get('/Filter')=='/FlateDecode' else raw
 def decode(self,font,data):
  mp=self.fonts[font]
  if mp is None:return data.decode('cp1252')
  assert len(data)%2==0
  return ''.join(mp[int.from_bytes(data[i:i+2],'big')] for i in range(0,len(data),2))
 def readpage(self,n):
  page=self.objects[n];fonts=self.deref(self.deref(page['/Resources'])['/Font']);c=page['/Contents'];contents=[c] if isinstance(c,tuple) else c
  data=b'\n'.join(self.stream(x[1]) for x in contents);p=Parser(data);args=[];stack=[];font=None;tm=None
  while True:
   try:x=p.val()
   except EOFError:break
   if not isinstance(x,str) or x.startswith('/'):
    args.append(x);continue
   if x=='BDC':stack.append(args[-1].get('/MCID') if isinstance(args[-1],dict) else None)
   elif x=='BMC':stack.append(None)
   elif x=='EMC':stack.pop()
   elif x=='Tf':font=fonts[args[0]][1]
   elif x=='Tm':tm=args[-6:]
   elif x in ('TJ','Tj'):
    items=args[-1] if x=='TJ' else [args[-1]]
    text=''.join(self.decode(font,i) for i in items if isinstance(i,bytes))
    mcid=next((v for v in reversed(stack) if v is not None),None)
    if mcid is not None:
     key=(n,mcid);self.mcids.setdefault(key,[]).append(text);self.runs.setdefault(key,[]).append({'font':font,'tm':tm,'text':text})
   elif x in ("'",'"'):raise ValueError('Unexpected text operator')
   args=[]
 def text(self,node,page=None):
  if isinstance(node,int):return ''.join(self.mcids.get((page,node),[]))
  if isinstance(node,list):return ''.join(self.text(x,page) for x in node)
  d=self.deref(node)
  if d.get('/Type')=='/MCR':return self.text(d['/MCID'],d.get('/Pg',('ref',page,0))[1])
  pg=d.get('/Pg',('ref',page,0))[1]
  return self.text(d.get('/K',[]),pg)
 def paragraphs(self,node,page=None):
  d=self.deref(node);pg=d.get('/Pg',('ref',page,0))[1];s=d.get('/S')
  if s in ('/P','/H1','/H2','/H3','/Caption','/Formula','/Figure'):
   text=self.text(node,page)
   yield {'object':node[1], 'type':s,'page':self.pages.get(pg),'text':text,'node':d}
   return
  k=d.get('/K',[]);k=k if isinstance(k,list) else [k]
  for child in k:
   if isinstance(child,tuple):yield from self.paragraphs(child,pg)

if __name__=='__main__':
 root=Path(__file__).resolve().parents[2]
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--out',type=Path,required=True,help='Fresh tagged-text JSON output')
 args=parser.parse_args()
 pdf=PDF(root/'paper/Certifying Behavior Without Hiding the Sandbox v1.pdf')
 rows=list(pdf.paragraphs(('ref',67,0)))
 args.out.parent.mkdir(parents=True,exist_ok=True)
 with args.out.open('x') as stream:
  stream.write(json.dumps(rows,ensure_ascii=False,indent=2,default=lambda x: x.decode('utf-16') if x.startswith(b'\xfe\xff') else x.decode('latin1'))+'\n')
 print(json.dumps({'status':'tagged_text_extracted','paragraphs':len(rows),'out':str(args.out),'rendering_verified':False}))
