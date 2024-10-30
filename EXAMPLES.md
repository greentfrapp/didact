# Examples

## Regular QA

Sample answer from PaperQA2 on "Final IncomeShield policy conditions 1 Sep 2024.pdf"

Question: "What am I covered for if I am warded in the hospital?"

Answer: "IncomeShield covers inpatient hospital treatment in MOH-accredited facilities, encompassing reasonable expenses for necessary medical treatment (Schedule2024 pages 3-4).  This includes daily ward and treatment charges for both normal wards and ICUs (Schedule2024 pages 4-6, Schedule2024 pages 11-13), surgical benefits (including day surgery, surgeon's fees, and anesthesia) (Schedule2024 pages 4-6, Schedule2024 pages 11-13), and surgical implants remaining in the body post-surgery (Schedule2024 pages 4-6).  Radiosurgery, including proton beam therapy (subject to MOH approval), is also covered (Schedule2024 pages 4-6).  Coverage for inpatient psychiatric treatment by a registered medical practitioner is included (Schedule2024 pages 9-11).  Pre- and post-hospitalization treatment are covered, up to 90 days before and after admission, respectively (Schedule2024 pages 4-6, Schedule2024 pages 9-11), with post-hospitalization treatment including physiotherapy, occupational therapy, speech therapy, and diagnostic services (Schedule2024 pages 6-7).  Prosthesis benefits are covered if resulting from limb or eye loss due to injury or illness (Schedule2024 pages 9-11).  Emergency overseas inpatient hospital treatment is covered for emergencies (Schedule2024 pages 9-11).  Specific coverage amounts depend on the chosen plan (Schedule2024 pages 3-4) and may be affected by the length of hospital stay (Schedule2024 pages 4-6).  Deductibles and co-insurance apply (Schedule2024 pages 11-13), except in cases of death during or within 30 days of discharge related to the hospitalization (Schedule2024 pages 9-11).  Payments are made directly to the hospital for electronic claims (Schedule2024 pages 11-13)."

## Contradiction Detection

Logs from PaperQA2 ContraCrow on "Final IncomeShield policy conditions 1 Sep 2024.pdf"

```
pqa --settings contracrow ask 'IncomeShield covers plastic surgery'
[13:41:21] New file to index: Final IncomeShield policy conditions 1 Sep        
           2024.pdf...                                                          
[13:41:27] SEMANTIC_SCHOLAR_API_KEY environment variable not set. Semantic      
           Scholar API rate limits may apply.                                   
           CROSSREF_MAILTO environment variable not set. Crossref API rate      
           limits may apply.                                                    
           CROSSREF_API_KEY environment variable not set. Crossref API rate     
           limits may apply.                                                    
[13:41:28] Metadata not found for Schedule of Benefits in                       
           SemanticScholarProvider.                                             
[13:41:30] Metadata not found for Schedule of Benefits in CrossrefProvider.     
[13:41:33] Complete (Schedule of Benefits).                                     
[13:41:34] Starting paper search for 'IncomeShield covers plastic surgery'.     
           paper_search for query 'IncomeShield covers plastic surgery' and     
           offset 0 returned 2 papers.                                          
           Status: Paper Count=2 | Relevant Papers=0 | Current Evidence=0 |     
           Current Cost=$0.0018                                                 
[13:41:35] gather_evidence starting for question 'IncomeShield covers plastic   
           surgery'.                                                            
[13:42:02] Status: Paper Count=2 | Relevant Papers=1 | Current Evidence=2 |     
           Current Cost=$0.1452                                                 
[13:42:03] Generating answer for 'IncomeShield covers plastic surgery'.         
[13:42:12] Status: Paper Count=2 | Relevant Papers=1 | Current Evidence=2 |     
           Current Cost=$0.1595                                                 
           Answer: <response>                                                   
             <reasoning>                                                        
           The claim that IncomeShield covers plastic surgery is contradicted by
           the context provided. The strongest evidence against this claim comes
           from Income2024 pages 19-20, which explicitly states under section   
           4.18 Exclusions, item c: 'Cosmetic surgery or any medical treatment  
           claimed to generally prevent illness, promote health or improve      
           bodily function or appearance' is not covered under the policy       
           (Income2024 pages 19-20). This directly excludes most forms of       
           plastic surgery.                                                     
                                                                                
           Additionally, Income2024 pages 23-24 provides a definition of        
           'necessary medical treatment' that suggests cosmetic plastic surgery 
           would not be covered, as it must be appropriate for treating an      
           illness or injury and not for convenience or promoting good health   
           (Income2024 pages 23-24). While this leaves open the possibility that
           reconstructive plastic surgery for medical reasons might be covered, 
           it still contradicts the broad claim that IncomeShield covers plastic
           surgery in general.                                                  
                                                                                
           None of the other excerpts provide evidence supporting coverage for  
           plastic surgery, and most do not mention it at all. The surgical     
           benefits mentioned in some excerpts do not specifically include or   
           exclude plastic surgery, but given the explicit exclusion mentioned  
           earlier, it's reasonable to conclude that IncomeShield generally does
           not cover plastic surgery.</reasoning>                               
             <label>strong contradiction</label>                                
           </response>   
```

```
pqa --settings contracrow ask 'IncomeShield covers prosthetics'
[14:23:44] Starting paper search for 'IncomeShield covers prosthetics'.         
           paper_search for query 'IncomeShield covers prosthetics' and offset 0
           returned 2 papers.                                                   
           Status: Paper Count=2 | Relevant Papers=0 | Current Evidence=0 |     
           Current Cost=$0.0018                                                 
[14:23:45] gather_evidence starting for question 'IncomeShield covers           
           prosthetics'.                                                        
[14:24:14] Status: Paper Count=2 | Relevant Papers=1 | Current Evidence=5 |     
           Current Cost=$0.1460                                                 
[14:24:15] Generating answer for 'IncomeShield covers prosthetics'.             
[14:24:24] Status: Paper Count=2 | Relevant Papers=1 | Current Evidence=5 |     
           Current Cost=$0.1596                                                 
           Answer: <response>                                                   
             <reasoning>The context provides strong evidence that IncomeShield  
           does indeed cover prosthetics. Multiple excerpts support this claim. 
           The schedule of benefits explicitly lists a "Prosthesis benefit" for 
           each policy year, with coverage amounts varying by plan (Income2024  
           pages 1-2). Detailed information about the prosthesis benefit is     
           provided, including eligibility criteria and coverage limits         
           (Income2024 pages 8-11). The policy defines "Prosthesis" as "an      
           artificial device extension that replaces any limb or eye of the     
           insured" (Income2024 pages 23-24). While there are some exclusions   
           mentioned for optional items and non-surgically necessary prostheses,
           the prosthesis benefit is specifically exempted from these exclusions
           (Income2024 pages 19-20). Additionally, the prosthesis benefit is    
           mentioned as being exempt from certain policy factors like the       
           citizenship factor and deductibles (Income2024 pages 20-23). This    
           consistent and detailed coverage of prosthetics across multiple      
           sections of the policy document strongly supports the claim that     
           IncomeShield covers prosthetics.</reasoning>                         
             <label>strong agreement</label>                                    
           </response>
```

```
pqa --settings contracrow ask 'IncomeShield covers lasik'
[14:28:50] Starting paper search for 'IncomeShield covers lasik'.               
           paper_search for query 'IncomeShield covers lasik' and offset 0      
           returned 2 papers.                                                   
           Status: Paper Count=2 | Relevant Papers=0 | Current Evidence=0 |     
           Current Cost=$0.0018                                                 
[14:28:52] gather_evidence starting for question 'IncomeShield covers lasik'.   
[14:29:20] Status: Paper Count=2 | Relevant Papers=1 | Current Evidence=1 |     
           Current Cost=$0.1445                                                 
[14:29:22] Generating answer for 'IncomeShield covers lasik'.                   
[14:29:30] Status: Paper Count=2 | Relevant Papers=1 | Current Evidence=1 |     
           Current Cost=$0.1582                                                 
           Answer: <response>                                                   
             <reasoning>                                                        
           The claim that IncomeShield covers lasik is explicitly contradicted  
           by the context provided. The most direct evidence comes from the     
           excerpt on pages 20-23, which clearly states that IncomeShield does  
           not cover "lasik treatments" under item ag in the list of exclusions.
           The policy specifically excludes "Routine eye and ear examinations,  
           correction for refractive errors of the eye (conditions such as      
           nearsightedness, farsightedness, presbyopia (gradual loss of the     
           eye's ability to focus on nearby objects) and astigmatism), lasik    
           treatments, costs of spectacles, costs of contact lenses and costs of
           hearing aid" (Income2024 pages 20-23). This unambiguous statement    
           directly contradicts the claim. None of the other excerpts provide   
           any evidence to support coverage for lasik treatments, and several   
           mention exclusions that could potentially apply to lasik, such as    
           cosmetic procedures and experimental treatments (Income2024 pages    
           19-20). The absence of any mention of lasik coverage in the benefits 
           sections further supports the conclusion that it is not covered      
           (Income2024 pages 2-4, Income2024 pages 1-2).</reasoning>            
             <label>explicit contradiction</label>                              
           </response>
```

## Quote Retrieval

```
koizumi2008adedicatedmri pages 2-3
[
    {'quote': 'Fermented soybean (natto)', 'point': 'Natto is identified as fermented soybeans.'},
    {'quote': '3D spin-echo    0.1     7     4      112 min/image set', 'point': 'Imaging parameters for natto before stirring included a 3D spin-echo method, TR of 0.1s, TE of 7ms, and an acquisition time of 112 minutes.'},
    {'quote': '3D spin-echo   1      40     4      1092 min/image set', 'point': 'Imaging parameters for natto after stirring included a 3D spin-echo method, TR of 1s, TE of 40ms, and an acquisition time of 1092 minutes.'}
]

koizumi2008adedicatedmri pages 5-7
[
    {'quote': 'Fermented soybean, natto, a traditional Japanese food, was measured by emphasising signals of the internal structures and oils concentration areas', 'point': 'Natto is identified as a traditional Japanese food made from fermented soybeans.'},
    {'quote': 'The surface of soybeans becomes ruffled and covered with dark gray-brown wrinkles, and a stringy material is observed on the bean surfaces when they are stirred using sticks.', 'point': 'The fermentation process gives natto a characteristic appearance and texture.'},
    {'quote': 'and swollen 2.5-times their original size were steamed, then incubated in a warm chamber (approximately 40°C) under aerobic conditions for approximately 20 h after being inoculated with Bacillus subtilis (natto).', 'point': 'The preparation process involves soaking, steaming, and incubation with Bacillus subtilis bacteria.'}
]

koizumi2008adedicatedmri pages 7-8
[
    {'quote': 'In the current investigation, the materials made by factory processes were obtained in a market.', 'point': 'The study used commercially produced natto.'},
    {'quote': 'The sticky materials outside beans (s) generated by fermentation (Muramatsu et al., 1997), which are made of γ-polyglutamic acid and β-2,6-fructan (levan) and are rich in free amino acid nutrients, were emphasised by T2-weighted images', 'point': 'Natto is made from fermented soybeans and has sticky materials outside the beans.'},
    {'quote': 'The moderate digestion of soybeans maintaining oil storing tissues and the generation of large amounts of sticky materials are the sources of the characteristic textural feel and taste of natto', 'point': 'The texture and taste of natto are due to the digestion of soybeans and the sticky materials.'}
]

koizumi2008adedicatedmri pages 9-9
[{'quote': 'Koizumi, M., Naito, S., Kano, H., Ishida, N. and Haishi, T. (2006b). Fermented soybeans, natto, observed by a compact MRI. The Food Industry, 49, 57-71 (in Japanese).', 'point': 'The study by Koizumi et al. (2006b) directly identifies natto as fermented soybeans.'}]

Question: What is natto?

Natto is a traditional Japanese food made from fermented soybeans (koizumi2008adedicatedmri pages 5-7 quote1, koizumi2008adedicatedmri pages 9-9 quote1).  The soybeans are soaked, steamed, and then incubated with *Bacillus subtilis* bacteria for approximately 20 hours at 40°C under aerobic conditions (koizumi2008adedicatedmri pages 5-7 quote3). This fermentation process results in a product with a characteristic ruffled surface, dark gray-brown wrinkles, and a stringy material when stirred (koizumi2008adedicatedmri pages 5-7 quote2).  The sticky material on the surface is composed of γ-polyglutamic acid and β-2,6-fructan (levan), and is rich in free amino acid nutrients (koizumi2008adedicatedmri pages 7-8 quote2).  MRI studies have shown that the internal structure of natto includes intensified cotyledons, vascular bundles, and oil-accumulating areas (koizumi2008adedicatedmri pages 7-8).  These features contribute to natto's unique textural feel and taste (koizumi2008adedicatedmri pages 7-8 quote3).  Studies have used MRI with varying repetition times (TR) and echo times (TE) to image natto before and after stirring (koizumi2008adedicatedmri pages 2-3).  One study used a TR of 0.1s and TE of 7ms (taking 112 minutes per image set) and another used a TR of 1s and TE of 40ms (taking 1092 minutes per image set) (koizumi2008adedicatedmri pages 2-3 quote2, koizumi2008adedicatedmri pages 2-3 quote3).
```
