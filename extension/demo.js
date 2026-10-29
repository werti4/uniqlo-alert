// Explicitly labeled design preview. This module never calls a remote service.
let data;
export function demoData() {
  const at = new Date().toISOString(), before = new Date(Date.now()-86400000*3).toISOString();
  const favorites = [
    {id:'E479219-000-01',url:'https://www.uniqlo.com/fr/fr/products/E479219-000/01',name:'Collants HEATTECH',image:'https://image.uniqlo.com/UQ/ST3/WesternCommon/imagesgoods/479219/item/goods_04_479219_3x4.jpg',color:'04 GRIS',size:'L',enabled:true,targetCents:null},
    {id:'E469847-000-00',url:'https://www.uniqlo.com/fr/fr/products/E469847-000/00',name:'Collant HEATTECH',image:null,color:'09 NOIR',size:'M',enabled:true,targetCents:null},
    {id:'E460527-000-00',url:'https://www.uniqlo.com/fr/fr/products/E460527-000/00',name:'Collant HEATTECH stretch',image:null,color:'09 NOIR',size:'L',enabled:false,targetCents:990}
  ].map((f,i) => ({...f,addedAt:new Date(Date.now()-i*100000).toISOString()}));
  data = {settings:{repo:'werti4/uniqlo-alert',branch:'main',token:'DEMONSTRATION-SANS-ACCES',key:''},favorites,dirty:false,syncedAt:at,cloud:{schema:1,lastScanAt:at,scanStats:{total:2,attempted:2,succeeded:2,failed:0,deferred:0},telegramConfigured:true,latestRun:{at,status:'completed',conclusion:'success'},products:{},alerts:[]}};
  for(let i=0;i<favorites.length;i++) {
    const f=favorites[i],price=[590,1490,1490][i];
    data.cloud.products[f.id]={...f,priceCents:price,regularCents:1490,firstPriceCents:1490,lowestCents:price,lastCheckedAt:at,status:'ok',sizes:['M','L','XL'],stockNote:'Tailles au catalogue ; stock par taille non vérifié',history:[{at:before,priceCents:1490},...(i===0?[{at,priceCents:590}]:[])]};
  }
  data.cloud.alerts=[{id:'demo',productId:favorites[0].id,name:favorites[0].name,url:favorites[0].url,at,oldCents:1490,newCents:590,delivery:'sent'}];
  return data;
}
export async function demoCall(type, values={}) {
  if(type==='read'||type==='sync') return data;
  if(type==='remove') data.favorites=data.favorites.filter(f=>f.id!==values.id);
  if(type==='update') Object.assign(data.favorites.find(f=>f.id===values.id),values.patch);
  if(type==='addUrl') {
    const {canonical}=await import('./core.js');const f=canonical(values.favorite.url);
    if(data.favorites.some(v=>v.id===f.id)) throw new Error('Cet article est déjà dans les favoris.');
    data.favorites.unshift({...f,name:values.favorite.name||'Article UNIQLO',enabled:true,color:'',size:'',targetCents:null});
  }
  if(['scan','publish','settings','reloadRemote'].includes(type)) throw new Error('Aperçu de démonstration : installez l’extension pour connecter GitHub.');
  data.dirty=true;return data;
}
