import requests
import os
from io import StringIO
import numpy as np
import re
import pandas as pd
from tqdm import tqdm

data_path = './NIST/'

elements = [
    "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne",
    "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar", "K", "Ca",
    "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
    "Ga", "Ge", "As", "Se", "Br", "Kr", "Rb", "Sr", "Y", "Zr",
    "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn",
    "Sb", "Te", "I", "Xe", "Cs", "Ba", "La", "Ce", "Pr", "Nd",
    "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb",
    "Lu", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg",
    "Tl", "Pb", "Bi", "Po", "At", "Rn", "Fr", "Ra", "Ac", "Th",
    "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm",
    "Md", "No", "Lr", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds",
    "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og"
]

atomic_numbers = list(np.arange(1, 119).astype(str))

def clean_element(s):
    if isinstance(s, float) and np.isnan(s):
        return np.nan
    match = re.match(r'^-?[\d.]+', str(s))
    return float(match.group()) if match else np.nan  # fallback to np.nan if no match

for a, e in tqdm(zip(atomic_numbers,elements)): 
    try:
        print('Pulling: '+e)
        if os.path.exists(data_path+a+'-'+e+'-lines.npy'):
            print('File '+e+' exits')
            continue
        URL = "https://physics.nist.gov/cgi-bin/ASD/lines1.pl?spectra="+str(e)
        URL += "&output_type=0&low_w=&upp_w=&unit=1&submit=Retrieve+Data&de=0&plot_out=0&"
        URL += "I_scale_type=1&format=3&line_out=0&remove_js=on&no_spaces=on&en_unit=0&output=0&page_size=15"
        URL += "&show_obs_wl=1&show_calc_wl=1&unc_out=1&order_out=0&max_low_enrg=&show_av=3&max_upp_enrg=&tsb_value=0&"
        URL += "min_str=&A_out=0&intens_out=on&max_str=&allowed_out=1&forbid_out=1&min_accur=&min_intens=&"
        URL += "conf_out=on&term_out=on&enrg_out=on&J_out=on"
        page = requests.get(URL)

        cleaned1 = page.text.replace('=','')
        cleaned2 = cleaned1.replace('"""""",','NaN,')
        cleaned3 = cleaned2.replace('"','')
        cleaned4 = cleaned3.replace('+\t','\t')

        csv_file = StringIO(cleaned4)
        df = pd.read_csv(csv_file,delimiter='\t',header=0)
        if len(list(df.columns)) < 3:
            raise Exception("Element not in NIST database")    
        
        clean_int = np.array([clean_element(s) for s in df['intens']], dtype=float)
        if len(clean_int[np.isfinite(clean_int)])<1:
            raise Exception("Element has no intentsity information")
        else:
            np.save(data_path+a+'-'+e+'-lines',df.to_records())
            print('Saved: '+e)
    except Exception as exc:
        print(exc)
        print('Failed: '+e)