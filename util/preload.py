js0 = '''() =>{ Object.defineProperty(navigator, 'webdriver',
{ get: () => false }
)}'''

js1 = '''() =>{Object.defineProperty(Notification, 'permission',
  {get:()=> 'default'}
)}'''

js2 = '''() =>{Object.defineProperty(navigator, 'platform',
  {get:()=> 'iOS'}
)}'''

js2_pc = '''() =>{Object.defineProperty(navigator, 'platform',
  {get:()=> 'MacIntel'}
)}'''

js3 = '''() =>{Object.defineProperty(navigator, 'appVersion',
  {get:()=>'5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1 (KHTML, like Gecko) CriOS/74.0.3729.169 Mobile/13B143 Safari/601.1.46'}
)}'''

js3_pc = '''() =>{Object.defineProperty(navigator, 'appVersion',
  {get:()=>'"5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"'}
)}'''

js4 = '''() =>{Object.defineProperty(navigator, 'language',
  {get:()=> 'zh'}
)}'''

js5 = '''() =>{Object.defineProperty(navigator, 'languages',
  {get:()=>['zh', 'zh-CN', 'en']}
)}'''

js7 = '''() =>{Object.defineProperty(navigator, 'plugins',
  {get:()=> [
    {
      description: 'Portable Document Format',
      filename: 'internal-pdf-viewer',
      name: 'Chrome PDF Plugin',
    },
    {
      description: '',
      filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
      name: 'Chrome PDF Viewer',
    }
  ]}
)}'''
