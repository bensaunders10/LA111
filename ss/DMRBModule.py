import pandas as pd
print("> Pandas version: ", pd.__version__)
pd.options.mode.chained_assignment = None
import numpy as np
from ipywidgets import Checkbox, Output, VBox, widgets, Layout, Box, Label
from os import listdir, mkdir, path
from os.path import isfile, join
from IPython.display import display, display_html, Markdown
from shutil import make_archive, rmtree
try:
	import geopandas as gpd
	print("> Geopandas version: ", gpd.__version__)
except ImportError:
	print("> Geopandas not installed. Shape files cannot be exported.")

def DisplayWebTAGTables(WebTAG1, WebTAG2, W):
    if W == 1:
        df1_styler = WebTAG1.style.set_table_attributes("style='display:block'") \
                    .set_caption("Opening year: no. of households experiencing 'without scheme' and 'with scheme' noise levels")
        df2_styler = WebTAG2.style.set_table_attributes("style='display:block'") \
                    .set_caption("Forecast year: no. of households experiencing 'without scheme' and 'with scheme' noise levels")
        display_html(df1_styler._repr_html_()+df2_styler._repr_html_(), raw=True)
    return()

def Main(inputloc, outputloc, LOAEL, SOAEL, NLOAEL, NSOAEL):
    out = Output()
    display(Markdown("<span style='color:red'>DMRB LA111 Processing Tool</span>"))
    def on_button_clicked(b):
        D, N, S, L, P, W, G = 0, 0, 0, 0, 0, 0, 0
        Columns, OColumns = [], []
        with out:
            out.clear_output()
            Fileoutput, val, D, N, S, L, P, W, G = Selection(FileList, Day, Night, ST, LT, PS, WT, GS, D, N, S, L, P, W, G)            
            if val == 1:
                print('Error')
            else:
                fullpath = inputloc+Fileoutput[0]
                Tab1 = ExcelRead(fullpath)
                Tab1, Columns, OColumns = AddColumns(Tab1,D,N,S,L) # Columns(Input, Day, Night, ST, LT)
                DMRB_ST, DMRB_LT, RelDF = LBCGC(Tab1, Columns, OColumns, D, N, S, L) #LBCGC(Tab1, Columns, OColumns, D, N, ST, LT)
                DisplayDMRBTables(DMRB_ST, DMRB_LT, S, L)
                AbsDF = AbsOut(Tab1, RelDF, OColumns, LOAEL, SOAEL, NLOAEL, NSOAEL, outputloc, D, N, S, L, G, P)
                WebTAG1, WebTAG2 = WebTAG(AbsDF, OColumns, W)
                DisplayWebTAGTables(WebTAG1, WebTAG2, W)
                print('\n> Process complete')
                                        
    Day = Checkbox(False, description='Day time')
    Night = Checkbox(False, description='Night time')
    ST = Checkbox(False, description='Short term')
    LT = Checkbox(False, description='Long term')
    WT = Checkbox(False, description='WebTAG')
    PS = Checkbox(False, description='Excel output')
    GS = Checkbox(False, description='Shapefile outputs')

    onlyfiles = [f for f in listdir(inputloc) if isfile(join(inputloc, f))]

    FileList = []
    for i, files in enumerate(onlyfiles):
        FileList.append(Checkbox(False, description=files))

    form_item_layout = Layout(
        display='flex',
        flex_flow='row',
        justify_content='space-between'
    )

    form_items = [
        Box([Label(value='Available files:'), VBox(FileList)], layout=form_item_layout),
        Box([Label(value='Scenario:'), VBox([Day, Night])], layout=form_item_layout)
    ]
    form_items2 = [
        Box([Label(value='LA111 table: '), VBox([ST, LT])], layout=form_item_layout),
        Box([Label(value='Processed data: '), VBox([PS])], layout=form_item_layout),
        Box([Label(value='WebTAG: '), VBox([WT])], layout=form_item_layout),
        Box([Label(value='GIS: '), VBox([GS])], layout=form_item_layout)
    ]
    form = Box(form_items, layout=Layout(
        display='flex',
        flex_flow='column',
        align_items='stretch',
        width='50%'
    ))
    form2 = Box(form_items2, layout=Layout(
        display='flex',
        flex_flow='column',
        align_items='stretch',
        width='50%'
    ))

    display(form, form2)   
    button = widgets.Button(description="Calculate")
    display(button)
    button.on_click(on_button_clicked)
    return(out)

def Selection(FileList, Day, Night, ST, LT, PS, WT, GS, D, N, S, L, P, W, G):
    Fileoutput = []
    val = 0
    t1, t2, t3, t4 = '','','',''
    for i, files in enumerate(FileList):
        if FileList[i].value == True:
            Fileoutput.append(FileList[i].description) 
    if len(Fileoutput) < 1:
        print('> Select a file')
        val = 1
    if len(Fileoutput) > 1:
        print('> Only one dataset can be processed at a time')
        val = 1
    if len(Fileoutput) == 1:
        print('> Reading: ', Fileoutput[0])
        if Day.value == True:
            D = 1
            t1 = 'day time'
        else:
            D = 0    
        if Night.value == True:
            N = 1
            if Day.value == True:
                t2 = ' and night time'
            else:
                t2 = 'night time'
        else:
            N = 0
        if ST.value == True:
            S = 1
            t3 = 'short term' 
        else:
            S = 0    
        if LT.value == True:
            L = 1
            if ST.value == True:
                t4 = ' and long term'
            else:
                t4 = 'long term'
        else:
            L = 0          
        if ST.value == False and LT.value == False:
            val = 1
            print('> Select short term or long term calculation')
        if Day.value == False and Night.value == False:
            val = 1 
            print('> Select Day or night time calculation')
        if val != 1:
            print('> Summarising ' + t1 + t2 + ' magnitude of impact over the ' + t3 + t4)
        if PS.value == True:
            P = 1
        else:
            P = 0   
        if WT.value == True:
            W = 1
        else:
            W = 0    
        if GS.value == True:
            G = 1
        else:
            G = 0   
    return(Fileoutput, val, D, N, S, L, P, W, G)

def WebTAG(dfInput, OColumns, W):
    if W == 1:
        df = dfInput[dfInput['SNSTV']=='RES'].reset_index()[OColumns]
        WT = [45,48,51,54,57,60,63,66,69,72,75,78,81]
        DMOdf = Tabular(df, 'DMO', OColumns, WT)
        DSOdf = Tabular(df, 'DSO', OColumns, WT)
        DMDdf = Tabular(df, 'DMD', OColumns, WT)
        DSDdf = Tabular(df, 'DSD', OColumns, WT)
        WTCat = ['<45','45-48','48-51','51-54','54-57','57-60','60-63','63-66','66-69','69-72','72-75','75-78','78-81','>=81']
        WebTAGdf1 = pd.DataFrame(columns=WTCat, index=WTCat)
        WebTAGdf2 = pd.DataFrame(columns=WTCat, index=WTCat)
        for column in WebTAGdf1:            
            for row in WebTAGdf1[column].iteritems():
                WebTAGdf1.loc[row[0],column] = np.sum((DMOdf.loc[:,column]==True)&(DSOdf.loc[:,row[0]]==True))
                WebTAGdf2.loc[row[0],column] = np.sum((DMDdf.loc[:,column]==True)&(DSDdf.loc[:,row[0]]==True))
    else:
        WebTAGdf1, WebTAGdf2 = 0, 0
    return(WebTAGdf1, WebTAGdf2)

def DisplayDMRBTables(DMRB_ST,DMRB_LT, S, L):
    DMRB_ST.fillna(0, inplace=True)
    DMRB_LT.fillna(0, inplace=True)
    Table1 = DMRB_ST.set_index('Change').rename_axis(None)
    Table2 = DMRB_LT.set_index('Change').rename_axis(None)
    df1_styler = Table1.style.set_table_attributes("style='display:inline'") \
                .set_caption('Short-term DMRB LA111 (Greatest change)') \
                .format({'ST Day RES': '{:,.0f}' \
                .format,'ST Day OSR': '{:,.0f}' \
                .format,'ST Night RES': '{:,.0f}' \
                .format,'ST Night OSR': '{:,.0f}'})
    df2_styler = Table2.style.set_table_attributes("style='display:inline'") \
                .set_caption('Long-term DMRB LA111 (Greatest change)') \
                .format({'LT Day RES': '{:,.0f}' \
                .format,'LT Day OSR': '{:,.0f}' \
                .format,'LT Night RES': '{:,.0f}' \
                .format,'LT Night OSR': '{:,.0f}'})
    if S == 1 and L == 1:
        display_html(df1_styler._repr_html_()+" "+df2_styler._repr_html_(), raw=True)
    if S == 1 and L == 0:
        display_html(df1_styler._repr_html_(), raw=True)
    if S == 0 and L == 1:
        display_html(df2_styler._repr_html_(), raw=True)
    return()

def DMRBChange(df, column, DT):
    df.loc[:,">=" + str(DT[0])]                    = (df[column] >= DT[0])
    df.loc[:,">=" + str(DT[1]) + "<" + str(DT[0])] = (df[column] < DT[0]) & (df[column] >= DT[1])
    df.loc[:,">=" + str(DT[2]) + "<" + str(DT[1])] = (df[column] < DT[1]) & (df[column] >= DT[2])
    df.loc[:,">" + str(DT[3]) + "<" + str(DT[2])] = (df[column] < DT[2]) & (df[column] > DT[3])
    df.loc[:,"=" + str(DT[3])]                     = (df[column] == DT[3])
    df.loc[:,">=" + str(DT[4]) + "<" + str(DT[3])]  = (df[column] > DT[4]) & (df[column] < DT[3])
    df.loc[:,">" + str(DT[5]) + "<=" + str(DT[4])] = (df[column] > DT[5]) & (df[column] <= DT[4])
    df.loc[:,">" + str(DT[6]) + "<=" + str(DT[5])] = (df[column] > DT[6]) & (df[column] <= DT[5])
    df.loc[:,"<=" + str(DT[6])]                    = (df[column] <= DT[6])
    return

def Tabular(df, column, OColumns, WT):
    LEQC = 2   # L10 to Leq16hr correction
    df.loc[:,"<" + str(WT[0])]              = (df[column] < WT[0]+LEQC)
    df.loc[:,str(WT[0]) + "-" + str(WT[1])] = (df[column] >= WT[0]+LEQC) & (df[column] < WT[1]+LEQC)
    df.loc[:,str(WT[1]) + "-" + str(WT[2])] = (df[column] >= WT[1]+LEQC) & (df[column] < WT[2]+LEQC)
    df.loc[:,str(WT[2]) + "-" + str(WT[3])] = (df[column] >= WT[2]+LEQC) & (df[column] < WT[3]+LEQC)
    df.loc[:,str(WT[3]) + "-" + str(WT[4])] = (df[column] >= WT[3]+LEQC) & (df[column] < WT[4]+LEQC)
    df.loc[:,str(WT[4]) + "-" + str(WT[5])] = (df[column] >= WT[4]+LEQC) & (df[column] < WT[5]+LEQC)
    df.loc[:,str(WT[5]) + "-" + str(WT[6])] = (df[column] >= WT[5]+LEQC) & (df[column] < WT[6]+LEQC)
    df.loc[:,str(WT[6]) + "-" + str(WT[7])] = (df[column] >= WT[6]+LEQC) & (df[column] < WT[7]+LEQC)
    df.loc[:,str(WT[7]) + "-" + str(WT[8])] = (df[column] >= WT[7]+LEQC) & (df[column] < WT[8]+LEQC)
    df.loc[:,str(WT[8]) + "-" + str(WT[9])] = (df[column] >= WT[8]+LEQC) & (df[column] < WT[9]+LEQC)
    df.loc[:,str(WT[9]) + "-" + str(WT[10])] = (df[column] >= WT[9]+LEQC) & (df[column] < WT[10]+LEQC)
    df.loc[:,str(WT[10]) + "-" + str(WT[11])] = (df[column] >= WT[10]+LEQC) & (df[column] < WT[11]+LEQC)
    df.loc[:,str(WT[11]) + "-" + str(WT[12])] = (df[column] >= WT[11]+LEQC) & (df[column] < WT[12]+LEQC)
    df.loc[:,">=" + str(WT[12])]              = (df[column] >= WT[12]+LEQC) 
    df = df[df.columns.difference(OColumns)]
    return(df)

def ExcelRead(path):
    xl = pd.ExcelFile(path)
    Tabstr = xl.sheet_names  # see all sheet names
    Tabs = []
    for count, i in enumerate(Tabstr):
        Tabs.append(xl.parse(Tabstr[count]))
    Tab1 = pd.DataFrame(Tabs[0])
    return(Tab1)

def AddColumns(X, D, N, S, L):
    if D not in [0,1] or N not in [0,1] or S not in [0,1] or L not in [0,1]:
        raise Exception('Include Columns(Input, D, N, ST, LT)')
    if D == 1 and N == 0 and S == 1 and L == 0:
        X.loc[:,'ST_CH'] = X['DSO']-X['DMO']
        X.loc[:,'ST_CH_GC'] = abs(X['ST_CH'])
    if D == 1 and N == 0 and S == 0 and L == 1:
        X.loc[:,'LT_CH'] = X['DSD']-X['DMO']
        X.loc[:,'LT_CH_GC'] = abs(X['LT_CH'])
    if D == 1 and N == 0 and S == 1 and L == 1:
        X.loc[:,'ST_CH'], X['LT_CH'] = X['DSO']-X['DMO'], X['DSD']-X['DMO']
        X.loc[:,'ST_CH_GC'], X['LT_CH_GC'] = abs(X['ST_CH']), abs(X['LT_CH'])
    if D == 0 and N == 1 and S == 1 and L == 0:
        X.loc[:,'N_ST_CH'] = X['DSON']-X['DMON']
        X.loc[:,'N_ST_CH_GC'] = abs(X['N_ST_CH'])
    if D == 0 and N == 1 and S == 0 and L == 1:
        X.loc[:,'N_LT_CH'] = X['DSDN']-X['DMON']
        X.loc[:,'N_LT_CH_GC'] = abs(X['N_LT_CH'])
    if D == 0 and N == 1 and S == 1 and L == 1:
        X.loc[:,'N_ST_CH'], X.loc[:,'N_LT_CH'] = X['DSON']-X['DMON'], X['DSDN']-X['DMON']
        X.loc[:,'N_ST_CH_GC'], X.loc[:,'N_LT_CH_GC'] = abs(X['N_ST_CH']), abs(X['N_LT_CH'])
    if D == 1 and N == 1 and S == 1 and L== 0:
        X.loc[:,'ST_CH'], X.loc[:,'N_ST_CH'] = X['DSO']-X['DMO'], X['DSON']-X['DMON']
        X.loc[:,'ST_CH_GC'], X.loc[:,'N_ST_CH_GC'] = abs(X['ST_CH']), abs(X['N_ST_CH'])
    if D == 1 and N == 1 and S == 0 and L == 1:
        X.loc[:,'LT_CH'], X.loc[:,'N_LT_CH'] = X['DSD']-X['DMO'], X['DSON']-X['DMON']
        X.loc[:,'LT_CH_GC'], X.loc[:,'N_LT_CH_GC'] =  abs(X['LT_CH']), abs(X['N_LT_CH'])
    if D == 1 and N == 1 and S == 1 and L == 1:
        X.loc[:,'ST_CH'], X.loc[:,'LT_CH'], X.loc[:,'N_ST_CH'], X.loc[:,'N_LT_CH'] = X['DSO']-X['DMO'], X['DSD']-X['DMO'], X['DSON']-X['DMON'], X['DSDN']-X['DMON']
        X.loc[:,'ST_CH_GC'], X.loc[:,'LT_CH_GC'], X.loc[:,'N_ST_CH_GC'], X.loc[:,'N_LT_CH_GC'] = abs(X['ST_CH']), abs(X['LT_CH']), abs(X['N_ST_CH']), abs(X['N_LT_CH'])
    OColumns = list(X.columns.difference(X.filter(regex='_GC',axis=1).columns)) # Columns without GC
    Columns = list(X.columns) # Columns with GC
    return(X, Columns, OColumns)

def LBCGC(Tab1, Columns, OColumns, D, N, S, L):
    Tab1 = np.round(Tab1,1)
    ST, LT = [5, 3, 1, 0, -1, -3, -5], [10, 5, 3, 0, -3, -5, -10]
   
    RelDF2 = pd.DataFrame(Tab1.drop_duplicates(subset="BLD", keep = "first"))
    RelDF = RelDF2[OColumns]
    RelDF.set_index('BLD', inplace=True)

    DMRB_ST = pd.DataFrame(columns=['ST Day RES', 'ST Day OSR', 'ST Night RES', 'ST Night OSR'])
    DMRB_LT = pd.DataFrame(columns=['LT Day RES', 'LT Day OSR', 'LT Night RES', 'LT Night OSR'])
    DMRB_ST.loc[:,'Change'] = ['<=-5','>-5<=-3', '>-3<=-1', '>=-1<0', '=0','>0<1','>=1<3','>=3<5','>=5']
    DMRB_LT.loc[:,'Change'] = ['<=-10','>-10<=-5', '>-5<=-3', '>=-3<0', '=0','>0<3','>=3<5','>=5<10','>=10']
    DMRB_ST.set_index(['Change'], inplace=True)
    DMRB_LT.set_index(['Change'], inplace=True)
    
    
    if S == 0 and L == 0:
        raise Exception('Short term or Long term input required LBCGC(Tab1, Columns, OColumns, D, N, ->ST, ->LT)')
    if D == 0 and N == 0:
        raise Exception('Day or Night input required LBCGC(Tab1, Columns, OColumns, ->D, ->N, ST, LT)')
        
    if D == 1 and S == 1:
        Tab1STGC1 = Tab1[Tab1['ST_CH_GC'] == Tab1.groupby('BLD')['ST_CH_GC'].transform('max')]
        Tab1STGC = pd.DataFrame(Tab1STGC1[Tab1STGC1['DSO'] == Tab1STGC1.groupby('BLD')['DSO'].transform('max')]).drop_duplicates(subset="BLD", keep = "first")
        Tab1STGC.set_index('BLD', inplace=True)
        RelDF.update(Tab1STGC['ST_CH'])
        Tab1STGCRES, Tab1STGCOSR = Tab1STGC[Tab1STGC['SNSTV']=='RES'], Tab1STGC[Tab1STGC['SNSTV']=='OSR']
        DMRBChange(Tab1STGCRES, 'ST_CH', ST)
        DMRBChange(Tab1STGCOSR, 'ST_CH', ST)
        STDayDwellGC = pd.DataFrame(Tab1STGCRES[Tab1STGCRES.columns.difference(Columns)].sum(), columns=['ST Day RES']).rename_axis('Change').reset_index()
        STDayOSRGC = pd.DataFrame(Tab1STGCOSR[Tab1STGCOSR.columns.difference(Columns)].sum(), columns=['ST Day OSR']).rename_axis('Change').reset_index()
        STDayDwellGC.set_index('Change', inplace=True)
        STDayOSRGC.set_index('Change', inplace=True)
        DMRB_ST.update(STDayDwellGC['ST Day RES'])
        DMRB_ST.update(STDayOSRGC['ST Day OSR'])
        
    if D == 1 and L == 1:    
        Tab1LTGC1 = Tab1[Tab1['LT_CH_GC'] == Tab1.groupby('BLD')['LT_CH_GC'].transform('max')]
        Tab1LTGC = pd.DataFrame(Tab1LTGC1[Tab1LTGC1['DSD'] == Tab1LTGC1.groupby('BLD')['DSD'].transform('max')]).drop_duplicates(subset="BLD", keep = "first")
        Tab1LTGC.set_index('BLD', inplace=True)
        RelDF.update(Tab1LTGC['LT_CH'])
        Tab1LTGCRES, Tab1LTGCOSR = Tab1LTGC[Tab1LTGC['SNSTV']=='RES'], Tab1LTGC[Tab1LTGC['SNSTV']=='OSR']
        DMRBChange(Tab1LTGCRES, 'LT_CH', LT)
        DMRBChange(Tab1LTGCOSR, 'LT_CH', LT)
        LTDayDwellGC = pd.DataFrame(Tab1LTGCRES[Tab1LTGCRES.columns.difference(Columns)].sum(), columns=['LT Day RES']).rename_axis('Change').reset_index()
        LTDayOSRGC = pd.DataFrame(Tab1LTGCOSR[Tab1LTGCOSR.columns.difference(Columns)].sum(), columns=['LT Day OSR']).rename_axis('Change').reset_index()
        LTDayDwellGC.set_index('Change', inplace=True)
        LTDayOSRGC.set_index('Change', inplace=True)
        DMRB_LT.update(LTDayDwellGC['LT Day RES'])
        DMRB_LT.update(LTDayOSRGC['LT Day OSR'])
        
    if N == 1 and S == 1:    
        Tab1NSTGC1 = Tab1[Tab1['N_ST_CH_GC'] == Tab1.groupby('BLD')['N_ST_CH_GC'].transform('max')]
        Tab1NSTGC = pd.DataFrame(Tab1NSTGC1[Tab1NSTGC1['DSON'] == Tab1NSTGC1.groupby('BLD')['DSON'].transform('max')]).drop_duplicates(subset="BLD", keep = "first")
        Tab1NSTGC.set_index('BLD', inplace=True)
        RelDF.update(Tab1NSTGC['N_ST_CH'])
        Tab1NSTGCRES, Tab1NSTGCOSR = Tab1NSTGC[Tab1NSTGC['SNSTV']=='RES'], Tab1NSTGC[Tab1NSTGC['SNSTV']=='OSR']
        DMRBChange(Tab1NSTGCRES, 'N_ST_CH', ST)
        DMRBChange(Tab1NSTGCOSR, 'N_ST_CH', ST)
        STNightDwellGC = pd.DataFrame(Tab1NSTGCRES[Tab1NSTGCRES.columns.difference(Columns)].sum(), columns=['ST Night RES']).rename_axis('Change').reset_index()
        STNightOSRGC = pd.DataFrame(Tab1NSTGCOSR[Tab1NSTGCOSR.columns.difference(Columns)].sum(), columns=['ST Night OSR']).rename_axis('Change').reset_index()
        STNightDwellGC.set_index('Change', inplace=True)
        STNightOSRGC.set_index('Change', inplace=True)
        DMRB_ST.update(STNightDwellGC['ST Night RES'])
        DMRB_ST.update(STNightOSRGC['ST Night OSR']) 
        
    if N == 1 and L == 1:     
        Tab1NLTGC1 = Tab1[Tab1['N_LT_CH_GC'] == Tab1.groupby('BLD')['N_LT_CH_GC'].transform('max')]
        Tab1NLTGC = pd.DataFrame(Tab1NLTGC1[Tab1NLTGC1['DSDN'] == Tab1NLTGC1.groupby('BLD')['DSDN'].transform('max')]).drop_duplicates(subset="BLD", keep = "first")
        Tab1NLTGC.set_index('BLD', inplace=True)
        RelDF.update(Tab1NLTGC['N_LT_CH'])
        Tab1NLTGCRES, Tab1NLTGCOSR = Tab1NLTGC[Tab1NLTGC['SNSTV']=='RES'], Tab1NLTGC[Tab1NLTGC['SNSTV']=='OSR']
        DMRBChange(Tab1NLTGCRES, 'N_LT_CH', LT)
        DMRBChange(Tab1NLTGCOSR, 'N_LT_CH', LT)
        LTNightDwellGC = pd.DataFrame(Tab1NLTGCRES[Tab1NLTGCRES.columns.difference(Columns)].sum(), columns=['LT Night RES']).rename_axis('Change').reset_index()
        LTNightOSRGC = pd.DataFrame(Tab1NLTGCOSR[Tab1NLTGCOSR.columns.difference(Columns)].sum(), columns=['LT Night OSR']).rename_axis('Change').reset_index()
        LTNightDwellGC.set_index('Change', inplace=True)
        LTNightOSRGC.set_index('Change', inplace=True)
        DMRB_LT.update(LTNightDwellGC['LT Night RES'])
        DMRB_LT.update(LTNightOSRGC['LT Night OSR'])
    
    DMRB_ST.loc["Total"] = DMRB_ST.sum()
    DMRB_LT.loc["Total"] = DMRB_LT.sum()
    DMRB_ST.reset_index(inplace=True)
    DMRB_LT.reset_index(inplace=True)
    return(DMRB_ST, DMRB_LT, RelDF)

def AbsOut(Tab1, RelDF, OColumns, LOAEL, SOAEL, NLOAEL, NSOAEL, outfile, D, N, S, L, G, P):
    AbsDF2 = pd.DataFrame(Tab1.drop_duplicates(subset="BLD", keep = "first"))
    AbsDF = AbsDF2[OColumns]
    AbsDF.set_index('BLD', inplace=True)
    
    
    
    #long term day
    if D == 1 and L == 1:
        Tab1DSDAbs1 = Tab1[Tab1['DSD'] == Tab1.groupby('BLD')['DSD'].transform('max')]
        Tab1DSDAbs = pd.DataFrame(Tab1DSDAbs1[Tab1DSDAbs1['LT_CH_GC'] == Tab1DSDAbs1.groupby('BLD')['LT_CH_GC'].transform('max')]).drop_duplicates(subset="BLD", keep = "first")
        Tab1DSDAbs.set_index('BLD', inplace=True)
        AbsDF.update(Tab1DSDAbs['DSD'])
        AbsDF.update(Tab1DSDAbs['DMD'])
    
    #short term day
    if D == 1 and S == 1:
        Tab1DSOAbs1 = Tab1[Tab1['DSO'] == Tab1.groupby('BLD')['DSO'].transform('max')]
        Tab1DSOAbs = pd.DataFrame(Tab1DSOAbs1[Tab1DSOAbs1['ST_CH_GC'] == Tab1DSOAbs1.groupby('BLD')['ST_CH_GC'].transform('max')]).drop_duplicates(subset="BLD", keep = "first")
        Tab1DSOAbs.set_index('BLD', inplace=True)
        AbsDF.update(Tab1DSOAbs['DSO'])
        AbsDF.update(Tab1DSOAbs['DMO'])
        

    #long term night
    if N == 1 and L == 1:
        Tab1DSDNAbs1 = Tab1[Tab1['DSDN'] == Tab1.groupby('BLD')['DSDN'].transform('max')]
        Tab1DSDNAbs = pd.DataFrame(Tab1DSDNAbs1[Tab1DSDNAbs1['N_LT_CH_GC'] == Tab1DSDNAbs1.groupby('BLD')['N_LT_CH_GC'].transform('max')]).drop_duplicates(subset="BLD", keep = "first")
        Tab1DSDNAbs.set_index('BLD', inplace=True)
        AbsDF.update(Tab1DSDNAbs['DSDN'])
        AbsDF.update(Tab1DSDNAbs['DMDN'])
        
    #short term night
    if N == 1 and S == 1:
        Tab1DSONAbs1 = Tab1[Tab1['DSON'] == Tab1.groupby('BLD')['DSON'].transform('max')]
        Tab1DSONAbs = pd.DataFrame(Tab1DSONAbs1[Tab1DSONAbs1['N_ST_CH_GC'] == Tab1DSONAbs1.groupby('BLD')['N_ST_CH_GC'].transform('max')]).drop_duplicates(subset="BLD", keep = "first")
        Tab1DSONAbs.set_index('BLD', inplace=True)
        AbsDF.update(Tab1DSONAbs['DSON'])
        AbsDF.update(Tab1DSDNAbs['DMON'])
            
    if D == 1 and S == 1:
        AbsDF.update(RelDF['ST_CH'])
        AbsDF.loc[:,'DSO_LOAEL'] = np.where((AbsDF.loc[:,'DSO']>=LOAEL) & (AbsDF['DSO']<SOAEL),'Yes','No')
        AbsDF.loc[:,'DSO_SOAEL'] = np.where(AbsDF.loc[:,'DSO']>=SOAEL,'Yes','No')
        AbsDF.loc[:,'DSO_NEW_LOAEL'] = np.where((AbsDF.loc[:,'DMO']<LOAEL) & (AbsDF['DSO']>=LOAEL),'Yes','No')
        AbsDF.loc[:,'DSO_NEW_SOAEL'] = np.where((AbsDF.loc[:,'DMO']<SOAEL) & (AbsDF['DSO']>=SOAEL),'Yes','No')
    if D == 1 and L == 1:
        AbsDF.update(RelDF['LT_CH'])
        AbsDF.loc[:,'DSD_LOAEL'] = np.where((AbsDF.loc[:,'DSD']>=LOAEL) & (AbsDF['DSD']<SOAEL),'Yes','No')
        AbsDF.loc[:,'DSD_SOAEL'] = np.where(AbsDF.loc[:,'DSD']>=SOAEL,'Yes','No')
        AbsDF.loc[:,'DSD_NEW_LOAEL'] = np.where((AbsDF.loc[:,'DMO']<LOAEL) & (AbsDF['DSD']>=LOAEL),'Yes','No')
        AbsDF.loc[:,'DSD_NEW_SOAEL'] = np.where((AbsDF.loc[:,'DMO']<SOAEL) & (AbsDF['DSD']>=SOAEL),'Yes','No')
    if N == 1 and S == 1:
        AbsDF.update(RelDF['N_ST_CH'])
        AbsDF.loc[:,'DSON_LOAEL'] = np.where((AbsDF.loc[:,'DSON']>=NLOAEL) & (AbsDF['DSON']<NSOAEL),'Yes','No')
        AbsDF.loc[:,'DSON_SOAEL'] = np.where(AbsDF.loc[:,'DSON']>=NSOAEL,'Yes','No')
        AbsDF.loc[:,'DSON_NEW_LOAEL'] = np.where((AbsDF.loc[:,'DMON']<NLOAEL) & (AbsDF['DSON']>=NLOAEL),'Yes','No')
        AbsDF.loc[:,'DSON_NEW_SOAEL'] = np.where((AbsDF.loc[:,'DMON']<NSOAEL) & (AbsDF['DSON']>=NSOAEL),'Yes','No')
    if N == 1 and L == 1: 
        AbsDF.update(RelDF['N_LT_CH'])
        AbsDF.loc[:,'DSDN_LOAEL'] = np.where((AbsDF.loc[:,'DSDN']>=NLOAEL) & (AbsDF['DSDN']<NSOAEL),'Yes','No')
        AbsDF.loc[:,'DSDN_SOAEL'] = np.where(AbsDF.loc[:,'DSDN']>=NSOAEL,'Yes','No')
        AbsDF.loc[:,'DSDN_NEW_LOAEL'] = np.where((AbsDF.loc[:,'DMON']<NLOAEL) & (AbsDF['DSDN']>=NLOAEL),'Yes','No')
        AbsDF.loc[:,'DSDN_NEW_SOAEL'] = np.where((AbsDF.loc[:,'DMON']<NSOAEL) & (AbsDF['DSDN']>=NSOAEL),'Yes','No')  

    if P == 1:
        print('> Saving excel file as output.xlsx')
        AbsDF.to_excel("Output/output.xlsx", sheet_name='Output')     

    if G == 1:
        print("> Creating and joining data to shape file")
        AbsDFgpd = gpd.GeoDataFrame(AbsDF, geometry=gpd.points_from_xy(AbsDF['X'], AbsDF['Y']), crs="epsg:27700")
        root = "Output"
        base = "zip"
        tempdir = root+"/"+base +"/"
        output_filename = "Output"
        basename = root+"/"+output_filename
        if path.exists(tempdir):
            try:
                rmtree(tempdir)
            except OSError as e:
                print("Error: %s : %s" % (tempdir, e.strerror))
            mkdir(tempdir)
            AbsDFgpd.to_file(tempdir+"Output.shp")
            print("> Compressing output to zip file: "+output_filename+".zip")
            make_archive(base_dir=base, root_dir=root, format='zip', base_name=basename)
        else:
            mkdir(tempdir)
            AbsDFgpd.to_file(tempdir+"Output.shp")
            print("> Saving "+output_filename+" as zip file")
            make_archive(base_dir=base, root_dir=root, format='zip', base_name=basename)
        try:
            rmtree(tempdir)
        except OSError as e:
            print("Error: %s : %s" % (tempdir, e.strerror))
    return(AbsDF)
