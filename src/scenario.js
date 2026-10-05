export const defaults = {station:'sz03',mode:'remote',server:'192.168.1.6',client:'192.168.1.103',user:'student',teleop:'/dev/ttyACM0',robot:'/dev/ttyACM1',teleopId:'leader-sz03',robotId:'follower-sz03',wrist:'0',front:'2',modelRoot:'/home/student/so101-models',model:'/workspace/models/aravindhs-NV/grootn16-finetune_sreetz-so101_teleop_vials_rack_left/checkpoint-10000',calibration:'/root/.cache/huggingface/lerobot/calibration/teleoperators/so101_leader/leader-sz03.json',viewer:'8203',tunnel:'18703',backend:'5500',simSource:'/home/xutao/so101-lab/so-101/Sim-to-Real-SO-101-Workshop/source'};
export function stationDefaults(station) {
 const n=Number(station.slice(2));
 return {teleopId:`leader-${station}`,robotId:`follower-${station}`,calibration:`/root/.cache/huggingface/lerobot/calibration/teleoperators/so101_leader/leader-${station}.json`,viewer:String(8200+n),tunnel:String(18700+n)};
}
export function migrateConfig(saved={}) {
 const c={...defaults,...saved};
 if(/^s\d{2}$/.test(c.station)) {
  c.station=`sz${c.station.slice(1)}`;
  Object.assign(c,stationDefaults(c.station),{backend:'5500'});
 }
 return c;
}
export function resolve(input={}) {
 const c={...defaults,...stationDefaults(input.station || defaults.station),...input};
 if(!/^sz(?:0[1-9]|[1-9][0-9])$/.test(c.station)) throw Error('工位 ID 应为 sz01–sz99。');
 if(!['remote','local'].includes(c.mode)) throw Error('请选择有效的算力场景。');
 for(const k of (c.mode==='remote'?['server','client']:['client'])) if(!/^[a-zA-Z0-9](?:[a-zA-Z0-9.-]{0,251}[a-zA-Z0-9])?$/.test(c[k])) throw Error('主机地址只填写 IPv4 或主机名，不含协议和端口。');
 if(!/^[a-z_][a-z0-9_-]*$/i.test(c.user)) throw Error('SSH 用户名无效。');
 for(const k of ['teleop','robot']) if(!/^\/dev\/[a-zA-Z0-9/_.-]+$/.test(c[k]) || c[k].includes('..')) throw Error('串口应为 /dev/ 下的设备路径。');
 if(c.teleop===c.robot) throw Error('主臂与从臂不能使用同一个串口。');
 for(const k of ['teleopId','robotId']) if(!/^[a-zA-Z0-9_-]+$/.test(c[k])) throw Error('校准 ID 只能包含字母、数字、下划线或连字符。');
 for(const k of ['wrist','front']) if(!/^\d{1,2}$/.test(String(c[k]))) throw Error('相机索引应为 0–99。');
 if(String(c.wrist)===String(c.front)) throw Error('两台相机的索引不能相同。');
 for(const k of ['viewer','tunnel','backend']) if(!/^\d+$/.test(String(c[k])) || +c[k]<1024 || +c[k]>65535) throw Error('端口范围应为 1024–65535。');
 for(const k of ['model','modelRoot','calibration','simSource']) if(!c[k].startsWith('/') || /[\r\n\x00]/.test(c[k])) throw Error('模型、校准文件与源码路径请填写绝对路径。');
 const n=Number(c.station.slice(2));
 c.port=5600+n;
 c.signal=String(49100+(n-1)*10);
 c.media=String(47998+(n-1)*10);
 if(new Set([c.port,+c.viewer,+c.tunnel,+c.backend,+c.signal,+c.media]).size!==6) throw Error('工位推理、网页、隧道、后端和信令/媒体端口不能冲突。');
 c.host=c.mode==='local'?'127.0.0.1':c.server;
 c.compute=c.mode==='local'?'本机 GPU':'集中服务器';
 c.cameras=JSON.stringify({wrist:{type:'opencv',index_or_path:Number(c.wrist),width:640,height:480,fps:30},front:{type:'opencv',index_or_path:Number(c.front),width:640,height:480,fps:30}});
 return c;
}
export const quote=value=>"'"+String(value).replaceAll("'","'\"'\"'")+"'";
export function render(template,c) {
 return template.replace(/\{\{(\w+)\}\}/g,(_,key)=>{if(!(key in c)) throw Error(`未知变量 ${key}`); return quote(c[key]);});
}
export function stepsFor(recipe,c) {return recipe.steps.filter(s=>!s.modes || s.modes.includes(c.mode)).map(s=>({...s,command:s.command?render(s.command,c):null,where:s.where.replaceAll('{compute}',c.compute)}));}
