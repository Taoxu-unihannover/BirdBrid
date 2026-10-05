import {quote,stepsFor} from './scenario.js';
const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

// Split the detailed guide once; it is the single source of lesson content.
export function lessonContent(recipe,c){
 const doc=new DOMParser().parseFromString(recipe.html,'text/html');
 const intro=[];const sections=[];let section=null;
 for(const node of doc.body.children){
  if(node.tagName==='H2'){section={id:node.id||`section-${sections.length}`,title:node.textContent,html:''};sections.push(section);}
  else if(section)section.html+=node.outerHTML;else intro.push(node.cloneNode(true));
 }
 const courseLinks=(items)=>'<ul>'+items.map(r=>`<li><a href="#/course/${escape(r.id)}">${String(r.order).padStart(2,'0')} · ${escape(r.title)}</a></li>`).join('')+'</ul>';
 const dependencies=`<h3>前置依赖课程</h3><p>${escape(recipe.prerequisite_note||'无前置课程。')}</p>${recipe.prerequisite_courses?.length?courseLinks(recipe.prerequisite_courses):''}${recipe.recommended_courses?.length?'<h3>建议先读（非必修）</h3>'+courseLinks(recipe.recommended_courses):''}`;
 const prerequisites=intro.filter(n=>n.tagName==='DETAILS').map(n=>{n.querySelector('summary')?.remove();return n.innerHTML;}).join('');
 const goals=sections.filter(s=>s.title==='学习目标').map(s=>s.html).join('');
 const summary=sections.filter(s=>/关键要点|避坑清单|参考资源|求助顺序/.test(s.title));
 const steps=sections.filter(s=>s.title!=='学习目标'&&!summary.includes(s));
 const overview=recipe.id==='02-setup'?goals:(intro.filter(n=>n.tagName!=='DETAILS').map(n=>n.outerHTML).join('')+goals);
 let selected=steps;
 if(recipe.id==='05-sim-teleop'){
  if(c.mode==='local')selected=steps.filter(s=>!/(登录服务器宿主机|建立主臂隧道|启动仿真容器|启动网页容器|进入仿真容器)/.test(s.title));
  else selected=steps.filter(s=>!s.title.includes('启动本机仿真'));
 }
 for(const s of selected){
  s.html=personalize(s.html,c);
  s.html=applyCommands(s.html,recipe,c);
  if(recipe.id==='05-sim-teleop'&&s.title.includes('观看与跟随检查')){
   const url=`http://${escape(c.host)}:${c.viewer}`;
   s.html+=`<p>本工位仿真地址（可复制到其他浏览器打开）：<code>${url}</code> <a class="simulation-link" target="_blank" rel="noopener" href="${url}">打开 ↗</a></p>`;
  }
 }
 return {preparation:[personalize(overview||`<p>${escape(recipe.description)}</p>`,c),dependencies+personalize(prerequisites?'<h3>设备与环境条件</h3>'+prerequisites:'',c)],steps:selected,notes:personalize(summary.map(s=>`<h3>${escape(s.title)}</h3>${s.html}`).join('')||'<p>操作完成后保存记录，按教师指引停止进程并整理设备。</p>',c)};
}

export function personalize(html,c){
 const doc=new DOMParser().parseFromString(html,'text/html');
 const map={'s03':c.station,'5582':String(c.port),'5554':String(c.backend),'8210':String(c.viewer),'18765':String(c.tunnel),'192.168.1.6':c.host};
 const walk=node=>{
  if(node.nodeType===3){node.textContent=node.textContent.replace(/192\.168\.1\.6|\bs03\b|\b(?:5582|5554|8210|18765)\b/g,v=>map[v]);}
  else for(const child of node.childNodes)walk(child);
 };walk(doc.body);
 doc.querySelectorAll('pre code').forEach(code=>{
  const vars={TELEOP_PORT:c.teleop,TELEOP_ID:c.teleopId,ROBOT_PORT:c.robot,ROBOT_ID:c.robotId,CAMERA_WRIST:c.wrist,CAMERA_FRONT:c.front};
  let text=code.textContent;
  for(const [key,value] of Object.entries(vars))text=text.replace(new RegExp(`(export ${key}=)[^\\s]+`,'g'),(_,prefix)=>prefix+quote(value));
  text=text.replace(/R07252801\.recalibrated\.json/g,quote(c.calibration)).replace(/(--robot_id\s+)R07252801/g,(_,prefix)=>prefix+quote(c.robotId)).replace(/你的账号@你的笔记本IP/g,`${quote(c.user)}@${quote(c.client)}`);
  if(/\$(?:TELEOP|ROBOT|CAMERA)_/.test(text)&&!text.includes('export TELEOP_PORT='))text=Object.entries(vars).map(([k,v])=>`export ${k}=${quote(v)}`).join('\n')+'\n\n'+text;
  code.textContent=text;
 });
 return doc.body.innerHTML;
}

// Reuse the tested recipe commands inside the detailed explanation, rather than
// rendering a second, duplicate list of command cards above the guide.
function applyCommands(html,recipe,c){
 const doc=new DOMParser().parseFromString(html,'text/html');
 const commands=stepsFor(recipe,c);
 const command=title=>commands.find(s=>s.title===title)?.command;
 for(const code of doc.querySelectorAll('pre code')){
  const text=code.textContent;let replacement;
  if(recipe.id==='02-setup'&&text.includes('docker run -d --name so101-client'))replacement=command('启动客户端');
  if(recipe.id==='03-calibration'){
   if(text.includes('lerobot-calibrate'))replacement=command(text.includes('--teleop.type')?'校准主臂':'校准从臂');
   if(text.includes('python')&&text.includes('so101_check_calibration.py'))replacement=command('校准结果检查');
  }
  if(recipe.id==='04-teleop'&&text.includes('lerobot-teleoperate'))replacement=command(text.includes('--robot.cameras')?'使用双相机遥操作':'启动主从跟随');
  if(recipe.id==='05-sim-teleop'){
  if(text.includes('python3 -u leader_server.py'))replacement=command('启动主臂读取服务');
  else if(text.includes('ssh -N'))replacement=command('建立主臂隧道');
  else if(text.includes('ssh sz03@'))replacement=command('登录服务器宿主机');
  else if(text.includes('docker run')&&text.includes('so101-sim'))replacement=command('启动仿真容器');
  else if(text.includes('docker run')&&text.includes('so101-web'))replacement=command('启动网页容器');
  else if(text.includes('docker exec')&&text.includes('so101-sim'))replacement=command('进入仿真容器');
  else if(text.includes('sim_to_real_so101.scripts.lerobot_agent')&&!text.includes('--repo_id'))replacement=command(c.mode==='local'?'启动本机仿真':'启动仿真');
 }
  if(recipe.id==='06-inference'&&text.includes('python station_server.py'))replacement=commands.find(s=>s.command?.includes('station_server.py'))?.command;
  if(recipe.id==='07-real-eval'&&text.includes('python so101_eval.py'))replacement=command('启动真机评估');
  if(recipe.id==='09-server-deploy'){
   if(text.includes('docker run')&&text.includes('--name so101-infer'))replacement=command('准备运行脚本')+'\n\n'+command('启动推理容器');
   if(text.includes('run_batched_server.py'))replacement=command('进入推理容器')+'\n\n'+command('启动批处理引擎');
  }
  if(replacement)code.textContent=replacement;
 }
 return doc.body.innerHTML;
}
