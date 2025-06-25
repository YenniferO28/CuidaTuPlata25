// js/colores.js

// Convierte HEX a HSL
function hexToHSL(H) {
  let r=0,g=0,b=0;
  if (H.length === 4) {
    r="0x"+H[1]+H[1]; g="0x"+H[2]+H[2]; b="0x"+H[3]+H[3];
  } else if (H.length === 7) {
    r="0x"+H[1]+H[2]; g="0x"+H[3]+H[4]; b="0x"+H[5]+H[6];
  }
  r/=255; g/=255; b/=255;
  const cMin = Math.min(r,g,b), cMax = Math.max(r,g,b), delta=cMax-cMin;
  let h=0, s=0, l=(cMax+cMin)/2;
  if (delta) {
    s = delta/(1-Math.abs(2*l-1));
    switch(cMax) {
      case r: h = ((g-b)/delta)%6; break;
      case g: h = (b-r)/delta + 2; break;
      case b: h = (r-g)/delta + 4; break;
    }
    h = Math.round(h*60);
    if (h<0) h+=360;
  }
  return {h, s: +(s*100).toFixed(1), l: +(l*100).toFixed(1)};
}

// Convierte HSL a HEX
function hslToHex(h, s, l) {
  s/=100; l/=100;
  const c = (1-Math.abs(2*l-1))*s,
        x = c*(1-Math.abs((h/60)%2-1)),
        m = l - c/2;
  let [r,g,b]=[0,0,0];
  if (h<60)      [r,g,b]=[c,x,0];
  else if (h<120)[r,g,b]=[x,c,0];
  else if (h<180)[r,g,b]=[0,c,x];
  else if (h<240)[r,g,b]=[0,x,c];
  else if (h<300)[r,g,b]=[x,0,c];
  else           [r,g,b]=[c,0,x];
  const toHex = v=>{
    const hex = Math.round((v+m)*255).toString(16);
    return hex.length===1 ? "0"+hex : hex;
  };
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

// Genera N tonos variando luminosidad
function generarTonosSimilares(hexColor, cantidad=5) {
  const {h,s,l} = hexToHSL(hexColor);
  const tonos=[]; 
  const paso = 40/(cantidad-1); 
  for (let i=0; i<cantidad; i++) {
    const nuevaL = Math.max(0, Math.min(100, l-20 + paso*i));
    tonos.push(hslToHex(h,s,nuevaL));
  }
  return tonos;
}

// Hacemos globales
window.generarTonosSimilares = generarTonosSimilares;
