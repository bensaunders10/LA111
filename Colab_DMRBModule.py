# issues / queries contact Ben Saunders (ben.saunders@wsp.com)
# version 4.2021B
import time
import pandas as pd
pd.options.mode.chained_assignment = None
import numpy as np
from ipywidgets import Checkbox, Output, VBox, widgets, Layout, Box, Label, HTML, Image
from os import listdir, mkdir, path
from os.path import isfile, join
from IPython.display import display, display_html

    # Main function (Main) that provides main loop for GUI elements. Inputs are the file input 
    # location, output location, and criteria parameters for LOAEL, SOAEL, NLOAEL and NSOAEL.
    # This function largely relates to the OPERATION of the software, and is not associated 
    # with any acoustic parameters or assumptions. 

def Main(filepath, LOAEL, SOAEL, NLOAEL, NSOAEL):
    inputloc,outputloc = FolderCheck(filepath)
    out = Output()
    def on_button_clicked(b):
        D, N, S, L, P, W, I, = 0, 0, 0, 0, 0, 0, 0
        Columns, OColumns = [], []
        with out:
            out.clear_output()
            Fileoutput, val, D, N, S, L, P, W, I = Selection(FileList, Day, Night, ST, LT, PS, WT, NIR, D, N, S, L, P, W, I)
            if val == 1:
                print('Error')
            else:
                fullpath = inputloc+'/'+Fileoutput[0]
                tic = time.clock()
                Tab1 = ExcelRead(fullpath)
                tic1 = time.clock()
                Tab1, Columns, OColumns = AddColumns(Tab1,D,N,S,L)
                DMRB_ST, DMRB_LT, RelDF, RelColumns = LBCGC(Tab1, Columns, OColumns, D, N, S, L)
                tic2 = time.clock()
                DisplayDMRBTables(DMRB_ST, DMRB_LT, S, L, out)
                AbsDF, AbsDFCol, NIRDF = AbsOut(Tab1, RelDF, OColumns, LOAEL, SOAEL, NLOAEL, NSOAEL, D, N, S, L, I)
                tic3 = time.clock()
                RelDF, WebTAG1, WebTAG2, WebTAGN1, WebTAGN2 = WebTAG(RelDF, OColumns, W, D, N)
                DisplayWebTAGTables(WebTAG1, WebTAG2, WebTAGN1, WebTAGN2, D, N, W)
                tic4 = time.clock()
                DataOutput(outputloc, AbsDF, AbsDFCol, RelDF, RelColumns, WebTAG1, WebTAG2, WebTAGN1, WebTAGN2, NIRDF, P, D, N, W, I)
                tic5 = time.clock()
                print('\n> Process complete')
                print('\n> Execution time: \n> Read data: ', round(tic1-tic,3),'seconds\n> Magnitude of change calculation: ', round(tic2-tic1,3), 'seconds\n> Absolute levels calculation: ', round(tic3-tic2,3), 'seconds\n> WebTAG calculation: ', round(tic4-tic3,3), 'seconds\n> Output / writing files: ', round(tic5-tic4,3), 'seconds')
                
    Day = Checkbox(False, description='Day time')
    Night = Checkbox(False, description='Night time')
    ST = Checkbox(False, description='Short term')
    LT = Checkbox(False, description='Long term')
    WT = Checkbox(False, description='WebTAG')
    NIR = Checkbox(False, description='Noise Insulation Regulations')
    PS = Checkbox(False, description='Excel output')

    onlyfiles = [f for f in listdir(inputloc) if isfile(join(inputloc, f))]

    FileList = []
    for i, files in enumerate(onlyfiles):
        FileList.append(Checkbox(False, description=files))

    form_item_layout = Layout(
        display='flex',
        flex_flow='row',
        justify_content='space-between'
    )
    
    title = widgets.HTML(value="<span style='color:red;font-size:16px'>DMRB LA111 Processing Tool</span>")
    wsp = Box([title], layout=form_item_layout)
    
    form_items = [
        Box([Label(value='Available files:'), VBox(FileList)], layout=form_item_layout),
        Box([Label(value='Scenario:'), VBox([Day, Night])], layout=form_item_layout)
    ]
    form_items2 = [
        Box([Label(value='LA111 table: '), VBox([ST, LT])], layout=form_item_layout),
        Box([Label(value='Further calculation: '), VBox([WT, NIR])], layout=form_item_layout),
        Box([Label(value='Output: '), VBox([PS])], layout=form_item_layout),
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

    display(wsp, form, form2)   
    button = widgets.Button(description="Calculate")
    display(button)
    button.on_click(on_button_clicked)
    return(out)


    # This function creates input and output folders if not found 
def FolderCheck(filepath):
    inputfol = 'Input'
    outputfol = 'Output'
    inputloc, outputloc = filepath+inputfol, filepath
    if not path.isdir(inputloc):
        mkdir(inputloc)
    if not path.isdir(outputloc):
        mkdir(outputloc)
    return(inputloc, outputloc)
    
    # This function (Selection) processes inputs from the user and outputs required 
    # parameters for other functions. It relates to the OPERATION of the software, and 
    # is not associated with any acoustic parameters or assumptions. 

def Selection(FileList, Day, Night, ST, LT, PS, WT, NIR, D, N, S, L, P, W, I):
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
            print('> Summarising ' + t1 + t2 + ' magnitude of impact over the ' + t3 + t4 + '\n')
        if PS.value == True:
            P = 1
        else:
            P = 0   
        if WT.value == True:
            W = 1
        else:
            W = 0    
        if NIR.value == True:
            I = 1
        else:
            I = 0   
        if NIR.value == True and ST.value == False:
            val = 1
            print('> Select short term for Noise Insulation calculation')
        if NIR.value == True and Day.value == False:
            val = 1
            print('> Select Day time for Noise Insulation calculation')
    return(Fileoutput, val, D, N, S, L, P, W, I)

    # This function (WebTAG) prepares the WebTAG table. Residential 'RES' rows are selected from 
    # the buidling evaluation data and are passed to the Tabular function that sorts values in
    # in 3dB catagories. The table (dataframe) is iterated over each row and column, and a  
    # comparison between DMOY - DSOY, DMFY - DSFY for the opening year and future year and returns the 
    # sum for each.
    
def WebTAG(dfInput, OColumns, W, D, N):
    if W == 1:
        df = dfInput[dfInput['SNSTV']=='RES'].reset_index()
        WT = [45,48,51,54,57,60,63,66,69,72,75,78,81]
        WTCat = ['<45','45-48','48-51','51-54','54-57','57-60','60-63','63-66','66-69','69-72','72-75','75-78','78-81','>=81']
        if D == 1:
            WebTAGdf1 = pd.DataFrame(columns=WTCat, index=WTCat)
            WebTAGdf2 = pd.DataFrame(columns=WTCat, index=WTCat)
            DMOYdf = Tabular(df, 'DMOY_WT', OColumns, WT, 'Day') # Do minimum opening year based on greatest short term change
            DSOYdf = Tabular(df, 'DSOY_WT', OColumns, WT, 'Day') # Do something opening year based on greatest short term change
            DMFYdf = Tabular(df, 'DMFY_WT', OColumns, WT, 'Day') # Do minimum future year based on greatest short term future year change
            DSFYdf = Tabular(df, 'DSFY_WT', OColumns, WT, 'Day') # Do something future year based on greatest short term future year change
            for column in WebTAGdf1:            
                for row in WebTAGdf1[column].iteritems():
                    WebTAGdf1.loc[column,row[0]] = np.sum((DMOYdf.loc[:,column]==True)&(DSOYdf.loc[:,row[0]]==True))
                    WebTAGdf2.loc[column,row[0]] = np.sum((DMFYdf.loc[:,column]==True)&(DSFYdf.loc[:,row[0]]==True))
        else:
            WebTAGdf1, WebTAGdf2 = 0, 0
        if N == 1:
            WebTAGNdf1 = pd.DataFrame(columns=WTCat, index=WTCat)
            WebTAGNdf2 = pd.DataFrame(columns=WTCat, index=WTCat)
            DMOYNdf = Tabular(df, 'DMOYN_WT', OColumns, WT, 'Night') # Do minimum opening year based on greatest short term change
            DSOYNdf = Tabular(df, 'DSOYN_WT', OColumns, WT, 'Night')
            DMFYNdf = Tabular(df, 'DMFYN_WT', OColumns, WT, 'Night') # Do minimum future year based on greatest FY-FY change
            DSFYNdf = Tabular(df, 'DSFYN_WT', OColumns, WT, 'Night')
            for column in WebTAGNdf1:
                for row in WebTAGNdf1[column].iteritems():
                    WebTAGNdf1.loc[column,row[0]] = np.sum((DMOYNdf.loc[:,column]==True)&(DSOYNdf.loc[:,row[0]]==True))
                    WebTAGNdf2.loc[column,row[0]] = np.sum((DMFYNdf.loc[:,column]==True)&(DSFYNdf.loc[:,row[0]]==True))
        else:
            WebTAGNdf1, WebTAGNdf2 = 0, 0
    else:
        WebTAGdf1, WebTAGdf2, WebTAGNdf1, WebTAGNdf2 = 0, 0, 0, 0
    return(dfInput, WebTAGdf1, WebTAGdf2, WebTAGNdf1, WebTAGNdf2)

    # This function (DisplayDMRBTables) styles pandas dataframes for CSS / HTML. It relates to the 
    # OPERATION of the software, and is not associated with any acoustic parameters or assumptions. 

def DisplayDMRBTables(DMRB_ST,DMRB_LT, S, L, out):   
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

    # This function (DisplayWebTAGTables) styles pandas dataframes for CSS / HTML. It relates to the 
    # OPERATION of the software, and is not associated with any acoustic parameters or assumptions. 
    
def DisplayWebTAGTables(WebTAG1, WebTAG2, WebTAGN1, WebTAGN2, D, N, W):
    print('\n')
    if D == 1:
        WebTAGOut1, WebTAGOut2 = WebTAG1, WebTAG2
    if N == 1 and D == 0:
        WebTAGOut1, WebTAGOut2 = WebTAGN1, WebTAGN2
    if W == 1:
        df1_styler = WebTAGOut1.style.set_table_attributes("style='display:block'") \
                    .set_caption("Opening year: no. of households experiencing 'without scheme' and 'with scheme' noise levels")
        df2_styler = WebTAGOut2.style.set_table_attributes("style='display:block'") \
                    .set_caption("Forecast year: no. of households experiencing 'without scheme' and 'with scheme' noise levels")
        display_html(df1_styler._repr_html_()+df2_styler._repr_html_(), raw=True)
    return()

    # The DMRBChange function catagorises changes by criteria set by the input. It accepts the
    # table (dataframe) as an input (df), followed by the column to be processed, and a 7
    # item list. For short term values: [5, 3, 1, 0, -1, -3, -5]

def DMRBCatagory(df, incolumn, outcolumn, DT):
    df.loc[(df[incolumn] >= DT[0]), outcolumn] = 'Major Adverse'
    df.loc[(df[incolumn] < DT[0]) & (df[incolumn] >= DT[1]), outcolumn] = 'Moderate Adverse'
    df.loc[(df[incolumn] < DT[1]) & (df[incolumn] >= DT[2]), outcolumn] = 'Minor Adverse'
    df.loc[(df[incolumn] < DT[2]) & (df[incolumn] > DT[3]), outcolumn] = 'Negligible Adverse'
    df.loc[(df[incolumn] == DT[3]), outcolumn] = 'No Change'
    df.loc[(df[incolumn] > DT[4]) & (df[incolumn] < DT[3]), outcolumn] = 'Negligible Beneficial'
    df.loc[(df[incolumn] > DT[5]) & (df[incolumn] <= DT[4]), outcolumn] = 'Minor Beneficial'
    df.loc[(df[incolumn] > DT[6]) & (df[incolumn] <= DT[5]), outcolumn] = 'Moderate Beneficial'
    df.loc[(df[incolumn] <= DT[6]), outcolumn] = 'Major Beneficial'
    
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

    # The Tabular function catagories changes by criteria set by the input for the WebTAG function. 
    # It accepts the table (dataframe) as an input (df), followed by the column to be processed (column), 
    # a filter column (the columns we want in the final output) and the item list. To produce WebTAG 
    # tables: WT = [45,48,51,54,57,60,63,66,69,72,75,78,81].
    # An Leq coreciton is also added LEQC = 2 to convert L10 to Leq16hr

def Tabular(df, column, OColumns, WT, DN):
    if DN == 'Day':
        LEQC = 2
    else:
        LEQC = 0
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

    # The ExcelRead function reads the excel file and converts it to a pandas dataframe. It relates 
    # to the  OPERATION of the software, and is not associated any acoustic parameters or assumptions. 

def ExcelRead(path):
    xl = pd.ExcelFile(path)
    Tabstr = xl.sheet_names  # see all sheet names
    Tabs = []
    for count, i in enumerate(Tabstr):
        Tabs.append(xl.parse(Tabstr[count]))
    Tab1 = pd.DataFrame(Tabs[0])
    return(Tab1)

    # The AddColumns function is called by the main function to add columns to the incoming dataframe, 
    # depending on the input values chosen. Two column filters Columns and OColumns (O = original), with 
    # and without the greatest change values are kept for further operations.

def AddColumns(X, D, N, S, L):
    OColumns = list(X.columns)
    if D not in [0,1] or N not in [0,1] or S not in [0,1] or L not in [0,1]:
        raise Exception('Include Columns(Input, D, N, ST, LT)')
    if D == 1 and N == 0 and S == 1 and L == 0:
        X.loc[:,'ST_CH'] = X['DSOY']-X['DMOY']
        X.loc[:,'ST_CH_GC'] = abs(X['ST_CH'])
        OColumns.extend(['ST_CH'])
    if D == 1 and N == 0 and S == 0 and L == 1:
        X.loc[:,'LT_CH'], X.loc[:,'DM_DM'], X.loc[:,'DMFY_DSFY'] = X['DSFY']-X['DMOY'], X['DMFY']-X['DMOY'], X['DSFY']-X['DMFY']
        X.loc[:,'LT_CH_GC'], X.loc[:,'DM_DM_GC'], X.loc[:,'DMFY_DSFY_GC'] = abs(X['LT_CH']), abs(X['DM_DM']), abs(X['DMFY_DSFY'])
        OColumns.extend(['LT_CH', 'DM_DM', 'DMFY_DSFY'])
    if D == 1 and N == 0 and S == 1 and L == 1:
        X.loc[:,'ST_CH'], X['LT_CH'], X.loc[:,'DM_DM'], X.loc[:,'DMFY_DSFY'] = X['DSOY']-X['DMOY'], X['DSFY']-X['DMOY'], X['DMFY']-X['DMOY'], X['DSFY']-X['DMFY']
        X.loc[:,'ST_CH_GC'], X['LT_CH_GC'], X.loc[:,'DM_DM_GC'], X.loc[:,'DMFY_DSFY_GC'] = abs(X['ST_CH']), abs(X['LT_CH']), abs(X['DM_DM']), abs(X['DMFY_DSFY'])
        OColumns.extend(['ST_CH', 'LT_CH', 'DM_DM'])
    if D == 0 and N == 1 and S == 1 and L == 0:
        X.loc[:,'N_ST_CH'] = X['DSOYN']-X['DMOYN']
        X.loc[:,'N_ST_CH_GC'] = abs(X['N_ST_CH'])
        OColumns.extend(['N_ST_CH'])
    if D == 0 and N == 1 and S == 0 and L == 1:
        X.loc[:,'N_LT_CH'], X.loc[:,'N_DM_DM'], X.loc[:,'DMFYN_DSFYN'] = X['DSFYN']-X['DMOYN'], X['DMFYN']-X['DMOYN'], X['DSFYN']-X['DMFYN']
        X.loc[:,'N_LT_CH_GC'], X.loc[:,'N_DM_DM_GC'], X.loc[:,'DMFYN_DSFYN_GC'] = abs(X['N_LT_CH']), abs(X['N_DM_DM']), abs(X['DMFYN_DSFYN'])
        OColumns.extend(['N_LT_CH', 'N_DM_DM', 'DMFYN_DSFYN'])
    if D == 0 and N == 1 and S == 1 and L == 1:
        X.loc[:,'N_ST_CH'], X.loc[:,'N_LT_CH'], X.loc[:,'N_DM_DM'], X.loc[:,'DMFYN_DSFYN'] = X['DSOYN']-X['DMOYN'], X['DSFYN']-X['DMOYN'], X['DMFYN']-X['DMOYN'], X['DSFYN']-X['DMFYN']
        X.loc[:,'N_ST_CH_GC'], X.loc[:,'N_LT_CH_GC'], X.loc[:,'N_DM_DM_GC'], X.loc[:,'DMFYN_DSFYN_GC'] = abs(X['N_ST_CH']), abs(X['N_LT_CH']), abs(X['N_DM_DM']), abs(X['DMFYN_DSFYN'])
        OColumns.extend(['N_ST_CH', 'N_LT_CH', 'N_DM_DM', 'DMFYN_DSFYN'])
    if D == 1 and N == 1 and S == 1 and L== 0:
        X.loc[:,'ST_CH'], X.loc[:,'N_ST_CH'] = X['DSOY']-X['DMOY'], X['DSOYN']-X['DMOYN']
        X.loc[:,'ST_CH_GC'], X.loc[:,'N_ST_CH_GC'] = abs(X['ST_CH']), abs(X['N_ST_CH'])
        OColumns.extend(['ST_CH', 'N_ST_CH'])
    if D == 1 and N == 1 and S == 0 and L == 1:
        X.loc[:,'LT_CH'], X.loc[:,'DM_DM'], X.loc[:,'DMFY_DSFY'], X.loc[:,'N_LT_CH'], X.loc[:,'N_DM_DM'], X.loc[:,'DMFYN_DSFYN'] = X['DSFY']-X['DMOY'], X['DMFY']-X['DMOY'], X['DSFY']-X['DMFY'], X['DSOYN']-X['DMOYN'], X['DMFYN']-X['DMOYN'], X['DSFYN']-X['DMFYN']
        X.loc[:,'LT_CH_GC'], X.loc[:,'DM_DM_GC'], X.loc[:,'DMFY_DSFY_GC'], X.loc[:,'N_LT_CH_GC'], X.loc[:,'N_DM_DM_GC'], X.loc[:,'DMFYN_DSFYN_GC'] =  abs(X['LT_CH']), abs(X['DM_DM']), abs(X['DMFY_DSFY']), abs(X['N_LT_CH']), abs(X['N_DM_DM']), abs(X['DMFYN_DSFYN'])
        OColumns.extend(['LT_CH', 'DM_DM', 'DMFY_DSFY', 'N_LT_CH', 'N_DM_DM', 'DMFYN_DSFYN'])
    if D == 1 and N == 1 and S == 1 and L == 1:
        X.loc[:,'ST_CH'], X.loc[:,'LT_CH'], X.loc[:,'DM_DM'], X.loc[:,'DMFY_DSFY'], X.loc[:,'N_ST_CH'], X.loc[:,'N_LT_CH'], X.loc[:,'N_DM_DM'], X.loc[:,'DMFYN_DSFYN'] = X['DSOY']-X['DMOY'], X['DSFY']-X['DMOY'], X['DMFY']-X['DMOY'], X['DSFY']-X['DMFY'], X['DSOYN']-X['DMOYN'], X['DSFYN']-X['DMOYN'], X['DMFYN']-X['DMOYN'], X['DSFYN']-X['DMFYN']
        X.loc[:,'ST_CH_GC'], X.loc[:,'LT_CH_GC'], X.loc[:,'DM_DM_GC'], X.loc[:,'DMFY_DSFY_GC'], X.loc[:,'N_ST_CH_GC'], X.loc[:,'N_LT_CH_GC'], X.loc[:,'N_DM_DM_GC'], X.loc[:,'DMFYN_DSFYN_GC'] = abs(X['ST_CH']), abs(X['LT_CH']), abs(X['DM_DM']), abs(X['DMFY_DSFY']), abs(X['N_ST_CH']), abs(X['N_LT_CH']), abs(X['N_DM_DM']), abs(X['DMFYN_DSFYN'])
        OColumns.extend(['ST_CH', 'LT_CH', 'DM_DM', 'DMFY_DSFY', 'N_ST_CH', 'N_LT_CH', 'N_DM_DM', 'DMFYN_DSFYN'])
    Columns = list(X.columns) # Columns are kept with GC
    return(X, Columns, OColumns)

    # The LBCGC function processes the incoming building evaluation data and calculates the greatest 
    # change in line with LA111. 
def LBCGC(Tab1, Columns, OColumns, D, N, S, L):
    Tab1 = np.round(Tab1,1)
    ST, LT = [5, 3, 1, 0, -1, -3, -5], [10, 5, 3, 0, -3, -5, -10]
       
    # A dummy dataset is created from the input and is filled by later operations. Building IDs 
    # in order + columns
    RelDF2 = pd.DataFrame(Tab1.drop_duplicates(subset="BLD", keep = "first"))
    RelDF = RelDF2[OColumns]
    RelDF.set_index('BLD', inplace=True)

    # A new dataframe is created for the short term and long term counts which will become the
    # DMRB tables.
    DMRB_ST = pd.DataFrame(columns=['ST Day RES', 'ST Day OSR', 'ST Night RES', 'ST Night OSR'])
    DMRB_LT = pd.DataFrame(columns=['LT Day RES', 'LT Day OSR', 'LT Night RES', 'LT Night OSR'])
    DMRB_ST.loc[:,'Change'] = ['<=-5','>-5<=-3', '>-3<=-1', '>=-1<0', '=0','>0<1','>=1<3','>=3<5','>=5']
    DMRB_LT.loc[:,'Change'] = ['<=-10','>-10<=-5', '>-5<=-3', '>=-3<0', '=0','>0<3','>=3<5','>=5<10','>=10']
    DMRB_ST.set_index(['Change'], inplace=True)
    DMRB_LT.set_index(['Change'], inplace=True)
    
    # Setting order of columns
    
    if D == 1 and S == 1: 
        RelDF['ST_Impact'] = ""
    if D == 1 and L == 1:
        RelDF['LT_Impact'] = ""
    if D == 1 and S == 1:
        RelDF['N_ST_Impact'] = ""
    if D == 1 and L == 1:
        RelDF['N_LT_Impact'] = ""

    RelColumns = list(RelDF.columns) # Columns for magnitude of impact output
    # error checking from input. We need short term or long term and day or night selected
    
    if S == 0 and L == 0:
        raise Exception('Short term or Long term input required LBCGC(Tab1, Columns, OColumns, D, N, ->ST, ->LT)')
    if D == 0 and N == 0:
        raise Exception('Day or Night input required LBCGC(Tab1, Columns, OColumns, ->D, ->N, ST, LT)')
        
    # The buidling evaluation data is 'grouped' by building and sorted ('transformed') by the  
    # maximum greatest change value (ST_CH_GC). To avoid duplicates, this is then sorted by the highest
    # value in the design variant, and then any remaining duplicates are dropped (by first value). 
    # The order is: Greatest change > Maximum absolute value > First remaining value.
    # The dummy dataset is then updated with the updated (greatest) ST_CH values
    # The data is then filtered by 'RES' and 'OSR' for residential and other sensitive receptors and then
    # passed to the DMRBChange function which sorts the short term changes into catagory columns. 
    # These are then summed for each column and then the new DMRB dataframe is updated. This process is then
    # repeated for short term / long term, day / night.
    
    if N == 1 and S == 1:    
        Tab1NSTGC1 = Tab1[Tab1['N_ST_CH_GC'] == Tab1.groupby('BLD')['N_ST_CH_GC'].transform('max')]
        Tab1NSTGC = pd.DataFrame(Tab1NSTGC1[Tab1NSTGC1['DSOYN'] == Tab1NSTGC1.groupby('BLD')['DSOYN'].transform('max')]).drop_duplicates(subset="BLD", keep = "first")
        Tab1NSTGC.set_index('BLD', inplace=True)
        RelDF.update(Tab1NSTGC['N_ST_CH'])
        RelDF['DMOYN_WT'] = Tab1NSTGC['DMOYN']  # for ST webtag calculation
        RelDF['DSOYN_WT'] = Tab1NSTGC['DSOYN']  # for ST webtag calculation
        #facade point values are copied in order of processing (Day long-term is prioritised and is updated last)
        RelDF.update(Tab1NSTGC[['X', 'Y', 'FAC', 'RCVR', 'DMOYN', 'DSOYN']])
        Tab1NSTGCRES, Tab1NSTGCOSR = Tab1NSTGC[Tab1NSTGC['SNSTV']=='RES'], Tab1NSTGC[Tab1NSTGC['SNSTV']=='OSR']
        DMRBChange(Tab1NSTGCRES, 'N_ST_CH', ST)
        DMRBChange(Tab1NSTGCOSR, 'N_ST_CH', ST)
        DMRBCatagory(RelDF, 'N_ST_CH', 'N_ST_Impact', ST)
        
        STNightDwellGC = pd.DataFrame(Tab1NSTGCRES[Tab1NSTGCRES.columns.difference(Columns)].sum(), columns=['ST Night RES']).rename_axis('Change').reset_index()
        STNightOSRGC = pd.DataFrame(Tab1NSTGCOSR[Tab1NSTGCOSR.columns.difference(Columns)].sum(), columns=['ST Night OSR']).rename_axis('Change').reset_index()
        STNightDwellGC.set_index('Change', inplace=True)
        STNightOSRGC.set_index('Change', inplace=True)
        DMRB_ST.update(STNightDwellGC['ST Night RES'])
        DMRB_ST.update(STNightOSRGC['ST Night OSR'])      
    
    if N == 1 and L == 1:     
        Tab1NLTGC1 = Tab1[Tab1['N_LT_CH_GC'] == Tab1.groupby('BLD')['N_LT_CH_GC'].transform('max')]
        Tab1NLTGC = pd.DataFrame(Tab1NLTGC1[Tab1NLTGC1['DSFYN'] == Tab1NLTGC1.groupby('BLD')['DSFYN'].transform('max')]).drop_duplicates(subset="BLD", keep = "first")       
        Tab1NLTGC.set_index('BLD', inplace=True)
        RelDF.update(Tab1NLTGC['N_LT_CH'])
        RelDF.update(Tab1NLTGC[['X', 'Y', 'FAC', 'RCVR', 'DMOYN', 'DMFYN', 'DSFYN']]) 
        Tab1NLTGCRES, Tab1NLTGCOSR = Tab1NLTGC[Tab1NLTGC['SNSTV']=='RES'], Tab1NLTGC[Tab1NLTGC['SNSTV']=='OSR']
        DMRBChange(Tab1NLTGCRES, 'N_LT_CH', LT)
        DMRBChange(Tab1NLTGCOSR, 'N_LT_CH', LT)
        
        #DM-DM greatest change night time (updating excel output only - not in tables)
        Tab1NDMGC1 = Tab1[Tab1['N_DM_DM_GC'] == Tab1.groupby('BLD')['N_DM_DM_GC'].transform('max')]
        Tab1NDMGC = pd.DataFrame(Tab1NDMGC1[Tab1NDMGC1['DMFYN'] == Tab1NDMGC1.groupby('BLD')['DSFYN'].transform('max')]).drop_duplicates(subset="BLD", keep = "first")       
        Tab1NDMGC.set_index('BLD', inplace=True)
        RelDF.update(Tab1NDMGC['N_DM_DM'])
        
        #DMFY-DSFY greatest change (updating excel output only - not in tables)
        Tab1NDMFYGC1 = Tab1[Tab1['DMFYN_DSFYN_GC'] == Tab1.groupby('BLD')['DMFYN_DSFYN_GC'].transform('max')]
        Tab1NDMFYGC = pd.DataFrame(Tab1NDMFYGC1[Tab1NDMFYGC1['DSFYN'] == Tab1NDMFYGC1.groupby('BLD')['DSFYN'].transform('max')]).drop_duplicates(subset="BLD", keep = "first")       
        Tab1NDMFYGC.set_index('BLD', inplace=True)
        RelDF['DMFYN_WT'] = Tab1NDMFYGC['DMFYN']  # for LT webtag calculation
        RelDF['DSFYN_WT'] = Tab1NDMFYGC['DSFYN']  # for LT webtag calculation
        RelDF.update(Tab1NDMFYGC['DMFYN_DSFYN'])
        DMRBCatagory(RelDF, 'N_LT_CH', 'N_LT_Impact', LT) # magnitude of impact category column
        
        LTNightDwellGC = pd.DataFrame(Tab1NLTGCRES[Tab1NLTGCRES.columns.difference(Columns)].sum(), columns=['LT Night RES']).rename_axis('Change').reset_index()
        LTNightOSRGC = pd.DataFrame(Tab1NLTGCOSR[Tab1NLTGCOSR.columns.difference(Columns)].sum(), columns=['LT Night OSR']).rename_axis('Change').reset_index()
        LTNightDwellGC.set_index('Change', inplace=True)
        LTNightOSRGC.set_index('Change', inplace=True)
        DMRB_LT.update(LTNightDwellGC['LT Night RES'])
        DMRB_LT.update(LTNightOSRGC['LT Night OSR'])

    if D == 1 and S == 1:
        Tab1STGC1 = Tab1[Tab1['ST_CH_GC'] == Tab1.groupby('BLD')['ST_CH_GC'].transform('max')] # greatest change
        Tab1STGC = pd.DataFrame(Tab1STGC1[Tab1STGC1['DSOY'] == Tab1STGC1.groupby('BLD')['DSOY'].transform('max')]).drop_duplicates(subset="BLD", keep = "first")
        Tab1STGC.set_index('BLD', inplace=True)
        RelDF.update(Tab1STGC['ST_CH'])
        RelDF['DMOY_WT'] = Tab1STGC['DMOY']  # for ST webtag calculation
        RelDF['DSOY_WT'] = Tab1STGC['DSOY']  # for ST webtag calculation
        RelDF.update(Tab1STGC[['X', 'Y', 'FAC', 'RCVR', 'DMOY', 'DSOY']])
        Tab1STGCRES, Tab1STGCOSR = Tab1STGC[Tab1STGC['SNSTV']=='RES'], Tab1STGC[Tab1STGC['SNSTV']=='OSR']
        DMRBChange(Tab1STGCRES, 'ST_CH', ST)
        DMRBChange(Tab1STGCOSR, 'ST_CH', ST)
        DMRBCatagory(RelDF, 'ST_CH', 'ST_Impact', ST)
        
        STDayDwellGC = pd.DataFrame(Tab1STGCRES[Tab1STGCRES.columns.difference(Columns)].sum(), columns=['ST Day RES']).rename_axis('Change').reset_index()
        STDayOSRGC = pd.DataFrame(Tab1STGCOSR[Tab1STGCOSR.columns.difference(Columns)].sum(), columns=['ST Day OSR']).rename_axis('Change').reset_index()
        STDayDwellGC.set_index('Change', inplace=True)
        STDayOSRGC.set_index('Change', inplace=True)
        DMRB_ST.update(STDayDwellGC['ST Day RES'])
        DMRB_ST.update(STDayOSRGC['ST Day OSR'])         
        
    if D == 1 and L == 1:    
        Tab1LTGC1 = Tab1[Tab1['LT_CH_GC'] == Tab1.groupby('BLD')['LT_CH_GC'].transform('max')]
        Tab1LTGC = pd.DataFrame(Tab1LTGC1[Tab1LTGC1['DSFY'] == Tab1LTGC1.groupby('BLD')['DSFY'].transform('max')]).drop_duplicates(subset="BLD", keep = "first")
        Tab1LTGC.set_index('BLD', inplace=True)
        RelDF.update(Tab1LTGC['LT_CH'])
        RelDF.update(Tab1LTGC[['X', 'Y', 'FAC', 'RCVR', 'DMOY', 'DMFY', 'DSFY']])
        Tab1LTGCRES, Tab1LTGCOSR = Tab1LTGC[Tab1LTGC['SNSTV']=='RES'], Tab1LTGC[Tab1LTGC['SNSTV']=='OSR']
        DMRBChange(Tab1LTGCRES, 'LT_CH', LT)
        DMRBChange(Tab1LTGCOSR, 'LT_CH', LT)
        DMRBCatagory(RelDF, 'LT_CH', 'LT_Impact', LT)
               
        #DM-DM greatest change (updating excel output only - not in tables)
        Tab1DMGC1 = Tab1[Tab1['DM_DM_GC'] == Tab1.groupby('BLD')['DM_DM_GC'].transform('max')]
        Tab1DMGC = pd.DataFrame(Tab1DMGC1[Tab1DMGC1['DMFY'] == Tab1DMGC1.groupby('BLD')['DMFY'].transform('max')]).drop_duplicates(subset="BLD", keep = "first")       
        Tab1DMGC.set_index('BLD', inplace=True)
        RelDF.update(Tab1DMGC['DM_DM'])
        
        #long term do minimum (DMFY-DSFY) greatest change (updating excel output only - not in tables)
        Tab1DMFYGC1 = Tab1[Tab1['DMFY_DSFY_GC'] == Tab1.groupby('BLD')['DMFY_DSFY_GC'].transform('max')]
        Tab1DMFYGC = pd.DataFrame(Tab1DMFYGC1[Tab1DMFYGC1['DSFY'] == Tab1DMFYGC1.groupby('BLD')['DSFY'].transform('max')]).drop_duplicates(subset="BLD", keep = "first")       
        Tab1DMFYGC.set_index('BLD', inplace=True)
        RelDF['DMFY_WT'] = Tab1DMFYGC['DMFY'] # For LT Webtag calculation
        RelDF['DSFY_WT'] = Tab1DMFYGC['DSFY'] # long term do minimum future year for WebTAG
        RelDF.update(Tab1DMFYGC['DMFY_DSFY'])
        
        LTDayDwellGC = pd.DataFrame(Tab1LTGCRES[Tab1LTGCRES.columns.difference(Columns)].sum(), columns=['LT Day RES']).rename_axis('Change').reset_index()
        LTDayOSRGC = pd.DataFrame(Tab1LTGCOSR[Tab1LTGCOSR.columns.difference(Columns)].sum(), columns=['LT Day OSR']).rename_axis('Change').reset_index()
        LTDayDwellGC.set_index('Change', inplace=True)
        LTDayOSRGC.set_index('Change', inplace=True)
        DMRB_LT.update(LTDayDwellGC['LT Day RES'])
        DMRB_LT.update(LTDayOSRGC['LT Day OSR'])
    
    # Once the DMRB dataframes are created, totals for each column are calculated. 
    DMRB_ST.loc["Total"] = DMRB_ST.sum()
    DMRB_LT.loc["Total"] = DMRB_LT.sum()
    DMRB_ST.reset_index(inplace=True)
    DMRB_LT.reset_index(inplace=True)
    return(DMRB_ST, DMRB_LT, RelDF, RelColumns)

    # AbsOut processes the absolute values from the buidling evaluation data and prepares  
    # the results for export to Excel
    # Noise insulation calculations are also processed in this function.
    
def AbsOut(Tab1, RelDF, OColumns, LOAEL, SOAEL, NLOAEL, NSOAEL, D, N, S, L, I):
    AbsDF2 = pd.DataFrame(Tab1.drop_duplicates(subset="BLD", keep = "first"))
    AbsDF = AbsDF2[OColumns]
    AbsDF.set_index('BLD', inplace=True)
    AbsDFCol = OColumns.copy()
    AbsDFCol.remove('BLD')
    NIRDF = Tab1[Tab1['SNSTV'] == 'RES']
            
    # To determine LOAEL and SOAELs:
    # Maximum absolute values for building maintained from DSFY and DSOY (Day and night) 
    # and results kept for a facade in pairs DSFY-DMFY, DSOY-DMOY, DSFYN-DMFYN, DSOYN-DMOYN 
    # This can be changed to the maximum value for every variant if preferred, however
    # this impacts the way in which NEW LOAELs and SOAELs are selectred.
    
    # The buidling evaluation data is 'grouped' by building and sorted ('transformed') by the  
    # maximum value in the design variant. To avoid duplicates, this is then sorted by the greatest
    # change, and then duplicates are dropped. So maximum absolute value > greatest change
    
    #short term night
    if N == 1 and S == 1:
        Tab1DSOYNAbs1 = Tab1[Tab1['DSOYN'] == Tab1.groupby('BLD')['DSOYN'].transform('max')]
        Tab1DSOYNAbs = pd.DataFrame(Tab1DSOYNAbs1[Tab1DSOYNAbs1['N_ST_CH_GC'] == Tab1DSOYNAbs1.groupby('BLD')['N_ST_CH_GC'].transform('max')]).drop_duplicates(subset="BLD", keep = "first")
        Tab1DSOYNAbs.set_index('BLD', inplace=True)
        AbsDF.update(Tab1DSOYNAbs['DSOYN'])
        AbsDF.update(Tab1DSOYNAbs['DMOYN']) # DMOYN maintained from DSOYN max filter
        AbsDF.update(Tab1DSOYNAbs[['X', 'Y', 'FAC', 'RCVR']])

    #long term night
    if N == 1 and L == 1:
        Tab1DSFYNAbs1 = Tab1[Tab1['DSFYN'] == Tab1.groupby('BLD')['DSFYN'].transform('max')] 
        Tab1DSFYNAbs = pd.DataFrame(Tab1DSFYNAbs1[Tab1DSFYNAbs1['N_LT_CH_GC'] == Tab1DSFYNAbs1.groupby('BLD')['N_LT_CH_GC'].transform('max')]).drop_duplicates(subset="BLD", keep = "first")
        Tab1DSFYNAbs.set_index('BLD', inplace=True)
        AbsDF.update(Tab1DSFYNAbs['DSFYN'])
        AbsDF.update(Tab1DSFYNAbs['DMFYN']) # DMFYN maintained from DSFYN max filter
        AbsDF.update(Tab1DSFYNAbs[['X', 'Y', 'FAC', 'RCVR']])
        
    #short term day
    if D == 1 and S == 1:
        Tab1DSOYAbs1 = Tab1[Tab1['DSOY'] == Tab1.groupby('BLD')['DSOY'].transform('max')] 
        Tab1DSOYAbs = pd.DataFrame(Tab1DSOYAbs1[Tab1DSOYAbs1['ST_CH_GC'] == Tab1DSOYAbs1.groupby('BLD')['ST_CH_GC'].transform('max')]).drop_duplicates(subset="BLD", keep = "first")
        Tab1DSOYAbs.set_index('BLD', inplace=True)
        AbsDF.update(Tab1DSOYAbs['DSOY'])
        AbsDF.update(Tab1DSOYAbs['DMOY']) # DMOY maintained from DSOY max filter
        AbsDF.update(Tab1DSOYAbs[['X', 'Y', 'FAC', 'RCVR']])
        
    #long term day
    if D == 1 and L == 1:
        Tab1DSFYAbs1 = Tab1[Tab1['DSFY'] == Tab1.groupby('BLD')['DSFY'].transform('max')] 
        Tab1DSFYAbs = pd.DataFrame(Tab1DSFYAbs1[Tab1DSFYAbs1['LT_CH_GC'] == Tab1DSFYAbs1.groupby('BLD')['LT_CH_GC'].transform('max')]).drop_duplicates(subset="BLD", keep = "first")
        Tab1DSFYAbs.set_index('BLD', inplace=True)
        AbsDF.update(Tab1DSFYAbs['DSFY'])
        AbsDF.update(Tab1DSFYAbs['DMFY']) # DMFY maintained from DSOY max filter
        AbsDF.update(Tab1DSFYAbs[['X', 'Y', 'FAC', 'RCVR']])

    # LOAEL and SOAELs are found when exceeding provided inputs 
    # These are tagged Yes/No in new columns: DSOY_LOAEL, DSOY_SOAEL etc. LOAEL/SOAEL 
    # in the DMOY is compared to the DSOY/DSFY and a NEW_SOAEL is found. 
    # > DMOY is the SAME FACADE as DSOY <

    if D == 1 and S == 1:
        AbsDF.update(RelDF['ST_CH'])
        AbsDF.loc[:,'DSOY_LOAEL'] = np.where((AbsDF.loc[:,'DSOY']>=LOAEL) & (AbsDF['DSOY']<SOAEL),'Yes','No')
        AbsDF.loc[:,'DSOY_SOAEL'] = np.where(AbsDF.loc[:,'DSOY']>=SOAEL,'Yes','No')
        AbsDF.loc[:,'DSOY_NEW_LOAEL'] = np.where((AbsDF.loc[:,'DMOY']<LOAEL) & (AbsDF['DSOY']>=LOAEL),'Yes','No')
        AbsDF.loc[:,'DSOY_NEW_SOAEL'] = np.where((AbsDF.loc[:,'DMOY']<SOAEL) & (AbsDF['DSOY']>=SOAEL),'Yes','No')
        AbsDFCol.extend(['DSOY_LOAEL','DSOY_SOAEL','DSOY_NEW_LOAEL','DSOY_NEW_SOAEL'])
    if D == 1 and L == 1:
        AbsDF.update(RelDF['LT_CH'])
        AbsDF.loc[:,'DSFY_LOAEL'] = np.where((AbsDF.loc[:,'DSFY']>=LOAEL) & (AbsDF['DSFY']<SOAEL),'Yes','No')
        AbsDF.loc[:,'DSFY_SOAEL'] = np.where(AbsDF.loc[:,'DSFY']>=SOAEL,'Yes','No')
        AbsDF.loc[:,'DSFY_NEW_LOAEL'] = np.where((AbsDF.loc[:,'DMOY']<LOAEL) & (AbsDF['DSFY']>=LOAEL),'Yes','No')
        AbsDF.loc[:,'DSFY_NEW_SOAEL'] = np.where((AbsDF.loc[:,'DMOY']<SOAEL) & (AbsDF['DSFY']>=SOAEL),'Yes','No')
        AbsDFCol.extend(['DSFY_LOAEL','DSFY_SOAEL','DSFY_NEW_LOAEL','DSFY_NEW_SOAEL'])
    if N == 1 and S == 1:
        AbsDF.update(RelDF['N_ST_CH'])
        AbsDF.loc[:,'DSOYN_LOAEL'] = np.where((AbsDF.loc[:,'DSOYN']>=NLOAEL) & (AbsDF['DSOYN']<NSOAEL),'Yes','No')
        AbsDF.loc[:,'DSOYN_SOAEL'] = np.where(AbsDF.loc[:,'DSOYN']>=NSOAEL,'Yes','No')
        AbsDF.loc[:,'DSOYN_NEW_LOAEL'] = np.where((AbsDF.loc[:,'DMOYN']<NLOAEL) & (AbsDF['DSOYN']>=NLOAEL),'Yes','No')
        AbsDF.loc[:,'DSOYN_NEW_SOAEL'] = np.where((AbsDF.loc[:,'DMOYN']<NSOAEL) & (AbsDF['DSOYN']>=NSOAEL),'Yes','No')
        AbsDFCol.extend(['DSOYN_LOAEL','DSOYN_SOAEL','DSOYN_NEW_LOAEL','DSOYN_NEW_SOAEL'])
    if N == 1 and L == 1: 
        AbsDF.update(RelDF['N_LT_CH'])
        AbsDF.loc[:,'DSFYN_LOAEL'] = np.where((AbsDF.loc[:,'DSFYN']>=NLOAEL) & (AbsDF['DSFYN']<NSOAEL),'Yes','No')
        AbsDF.loc[:,'DSFYN_SOAEL'] = np.where(AbsDF.loc[:,'DSFYN']>=NSOAEL,'Yes','No')
        AbsDF.loc[:,'DSFYN_NEW_LOAEL'] = np.where((AbsDF.loc[:,'DMOYN']<NLOAEL) & (AbsDF['DSFYN']>=NLOAEL),'Yes','No')
        AbsDF.loc[:,'DSFYN_NEW_SOAEL'] = np.where((AbsDF.loc[:,'DMOYN']<NSOAEL) & (AbsDF['DSFYN']>=NSOAEL),'Yes','No')  
        AbsDFCol.extend(['DSFYN_LOAEL','DSFYN_SOAEL','DSFYN_NEW_LOAEL','DSFYN_NEW_SOAEL'])
    if I == 1 and D == 1:
        NIRDF = NIRDF[OColumns]
        NIRDF.set_index('RCVR', inplace=True)
        NIRDF['Condition1'] = np.where(NIRDF.loc[:,'DSOY']>=67.5,'Yes','No')
        NIRDF['Condition2'] = np.where((NIRDF['Condition1'] == 'Yes') & (NIRDF.loc[:,'ST_CH']>=0.5),'Yes','No')
        Condition1 = NIRDF[NIRDF['Condition1'] == 'Yes'].drop_duplicates(subset="BLD", keep = "first").shape[0]
        Condition2 = NIRDF[NIRDF['Condition2'] == 'Yes'].drop_duplicates(subset="BLD", keep = "first").shape[0]
        NIRDF = NIRDF[NIRDF['Condition1'] == 'Yes']
        NIRDF = pd.DataFrame(NIRDF[NIRDF['ST_CH'] == NIRDF.groupby('BLD')['ST_CH'].transform('max')]).drop_duplicates(subset="BLD", keep = "first")
        print('\n> Calculating noise insulation.')
        print('> Dwellings exceeding 68dB in DSOY on any facade: ', str(Condition1))
        print('> Dwellings exceeding 68dB in DSOY and >= 1dB ST change on same facade: ', str(Condition2))   
    return(AbsDF, AbsDFCol, NIRDF)

# DataOutput saves results to excel
def DataOutput(outputloc, AbsDF, AbsDFCol, RelDF, RelColumns, WebTAG1, WebTAG2, WebTAGN1, WebTAGN2, NIRDF, P, D, N, W, I):
    if P == 1:
        print('> Saving data to output.xlsx')
        AbsDFOut = AbsDF[AbsDFCol]
        RelDFOut = RelDF[RelColumns]
        with pd.ExcelWriter(outputloc+"Output/output.xlsx", engine='openpyxl') as writer:  
            AbsDFOut.to_excel(writer, sheet_name='Highest absolute levels')
            print('> ... Highest absolute levels')
            RelDFOut.to_excel(writer, sheet_name='Magnitude of Impact')
            print('> ... Magnitude of Impact')
            if W ==1:
                print('> ... WebTAG tables')
                colvard = 35 if N == 1 else 18
                colvarn = 18 if D == 1 else 1
                colverr = 52 if D == 1 else 18
                if D == 1:
                    WebTAG1.to_excel(writer, sheet_name='WebTAG', startrow=1)
                    ws = writer.sheets['WebTAG']
                    ws.cell(row=1, column=1).value = "Opening year: no. of households experiencing 'without scheme' and 'with scheme' noise levels"
                    ws.cell(row=2, column=1).value = "dB (LAeq,16hr)"
                    ws.cell(row=colvard, column=1).value = "Forecast year: no. of households experiencing 'without scheme' and 'with scheme' noise levels"
                    ws.cell(row=colvard+1, column=1).value = "dB (LAeq,16hr)"
                    WebTAG2.to_excel(writer, sheet_name='WebTAG', startrow=colvard)
                if N == 1:
                    WebTAGN1.to_excel(writer, sheet_name='WebTAG', startrow=colvarn)
                    ws = writer.sheets['WebTAG']
                    ws.cell(row=colvarn, column=1).value = "Opening year: no. of households experiencing 'without scheme' and 'with scheme' noise levels"
                    ws.cell(row=colvarn+1, column=1).value = "dB (Lnight)"
                    ws.cell(row=colverr, column=1).value = "Forecast year: no. of households experiencing 'without scheme' and 'with scheme' noise levels"       
                    ws.cell(row=colverr+1, column=1).value = "dB (Lnight)"
                    WebTAGN2.to_excel(writer, sheet_name='WebTAG', startrow=colverr)
            if I ==1:
                print('> ... buildings with facades exceeding 67.5dB (maximum short term change exported)')
                NIRDF.to_excel(writer, sheet_name='Noise Insulation', startrow=0)

