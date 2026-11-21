import pyarrow 
import pandas as pd
import numpy as np
import matplotlib





# from myUtils import print_in_box ,  printMetaDataToken , getUserInput , printReqMetaDataToken
# from myUtils import color_user, color_llm  ,config , Fore 
# from myUtils import BASE_DIR, CONFIG_DIR, CONFIG_FILE

# import configparser
import os 
from datetime import datetime ,  date, timedelta
import sys
import fnmatch
from tabulate import tabulate
import warnings
# from pandas.errors import SettingWithCopyWarning

# Local imports
try:
    from myUtils import (
        print_in_box,
        printMetaDataToken,
        getUserInput,
        printReqMetaDataToken,
        color_user,
        color_llm,
        config,
        Fore,
        BASE_DIR,
        CONFIG_DIR,
        CONFIG_FILE
    )
except ImportError:
    # Fallback if myUtils is not available (e.g. for standalone testing)
    import configparser

    config = configparser.ConfigParser()
    config.read("config.ini")

    def print_in_box(msg, color="YELLOW"): print(f"[{color}] {msg}")
    flagDebug = False
    flagFlow = False
    flagPlot = False


# import warnings
# from pandas.errors import SettingWithCopyWarning
# warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)
# warnings.filterwarnings('ignore', category=FutureWarning )


# From COnfig
# Configuration Loading
try:
    flagDebug = config.getboolean("SETTINGS", "debug")
    flagFlow = config.getboolean("SETTINGS", "flow")
    
    flagPlot = config.getboolean("EXP", "plotting")
    filePath = config["EXP"]["filePath"]
    home_directory = os.path.expanduser('~')
    filePath = os.path.join(home_directory, filePath)

    fileName = config["EXP"]["fileName"]
    daysInPast_raw = config["EXP"].get("daysInPast", "90")
    daysInPast = int(daysInPast_raw) if daysInPast_raw else 90
    
    printForXls = config.getboolean("EXP", "printForXls")
    printForAnalysis = config.getboolean("EXP", "printForAnalysis")
except Exception as e:
    print(f"Error loading configuration: {e}")
    sys.exit(1)


# Matplotlib setup
if flagPlot:
    import matplotlib
    import tkinter as tk  # installed using apt
    matplotlib.use('TkAgg')


# generic
DT_FORMAT = "%Y-%m-%d %H:%M:%S"
COL_AMOUNT = "Expenses"
COL_TOTAL = "Total"
zFlow = "\n>>>> "
COL_COLUMN = ""

LIST_MONTHLY = ['Monthly','Donation']
LIST_EXCLUDE = ['EMI']
LIST_GROUP_BY = ['YearMonth' , 'WeekNum']
LIST_DISPLAY = [ 'Date', COL_AMOUNT , 'Title', 'Category', 'Account', 'Labels'  ]
LIST_SHORT_DISPLAY = [COL_AMOUNT , 'Title']

weekday_mapping = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 7}

pd.options.display.float_format = '{:,.2f}'.format


## columns=COL_COLUMN ,
def amountsSummaryByMonth(dfCsv):

    # print("\n\n----------------------------------------")
    print_in_box("Amounts by Month are as below:")

    listGraphCols = []

    # colIndex = ['YearMonth' , 'Type'  ]
    colIndex = [ 'YearMonth'  ]
    COL_COLUMN = ['Type']

    t = pd.DataFrame()
    t = dfCsv.pivot_table(index = colIndex , values = COL_AMOUNT ,  columns = COL_COLUMN ,
                          aggfunc = "sum" , margins = False  , fill_value = 0 ) 

   

    t.loc['Total',:] = t.sum(axis = 0)
    t.loc[ :,'Savings'] = t.sum(axis = 1)

    for i in t.columns:
        listGraphCols.append(t[i].name)
        if "Exp" in t[i].name:
            t[i] = t[i] * -1 

        t[i] = t[i].astype(float)
        
    t.reset_index(drop = False, names = colIndex, inplace=True)    
    t.fillna(value=0 , inplace=True)

    if flagPlot:
        pltX = colIndex[0]
        pltY = listGraphCols
        t.plot(x=pltX , y=pltY , kind='bar')
        plt.title("Income vs Expense per month")
        plt.xlabel('Year-Month')
        plt.ylabel("Amount in Rs")
        plt.show() 

    # print(t.to_string(index=False))
    # print("----------------------------------------")
    print(tabulate(t, headers='keys', tablefmt='outline', showindex=False, floatfmt=',.2f', numalign="right"))
    





def amtByMonth(dfCsv , strType):

    # print("\n\n----------------------------------------")
    curr_color = "GREEN" if strType.upper() == "INCOME" else "RED"
    print_in_box(f"{strType} by Month are as below:", curr_color)

    colIndex = ['YearMonth'  ]
    t = pd.DataFrame()
    t = dfCsv.pivot_table(index = colIndex , values = COL_AMOUNT 
                          , aggfunc = "sum" , margins = False  , fill_value = 0 ) 
    

    t[COL_AMOUNT] = t[COL_AMOUNT].astype(float)
    meanValue = t[COL_AMOUNT].mean()
    totalValue = t[COL_AMOUNT].sum()

    print("Summary --> monthly Mean {:,.2f} - Total {:,.2f} \n".format(meanValue , totalValue))

    t = t.reset_index(drop = False, names = colIndex)    

    # for i in t.index:
    #     t.loc[i, 'Delta_from_Mean'] = (t.loc[i,COL_AMOUNT] - meanValue )

    #     if i == 0:
    #         t.loc[i, 'Delta'] = 0
    #     else:
    #         diff_amount = t.loc[i,COL_AMOUNT] - t.loc[i-1 ,COL_AMOUNT ]
    #         t.loc[i, 'Delta'] = diff_amount

    t['Delta_from_Mean'] = t[COL_AMOUNT] - meanValue
    t['Delta'] = t[COL_AMOUNT].diff().fillna(0) 
            
    i = t.index[-1]
    t.loc[i+1, colIndex] = 'Total'
    t.loc[i+1, COL_AMOUNT] = totalValue


    t.fillna(value=0 , inplace=True)
    # t[COL_AMOUNT] = t[COL_AMOUNT].apply('{:,.2f}'.format)
    # t['Delta'] = t['Delta'].apply('{:,.2f}'.format)
    # t['Delta_from_Mean'] = t['Delta_from_Mean'].apply('{:,.2f}'.format)

    # renaming column to income or expense, based on var value
    t = t.rename(columns = {COL_AMOUNT : strType})

    # print(t.to_string(index=False))
    # print("----------------------------------------")
    print(tabulate(t, headers='keys', tablefmt='outline', showindex=False, floatfmt=',.2f', numalign="right"))




# def expByMonth(dfCsv):

#     print("\n\n----------------------------------------")
#     print("XXX Expenses by Month are as below:")

#     colIndex = ['YearMonth'  ]
#     t = dfCsv.pivot_table(index = colIndex , values = COL_AMOUNT 
#                           , aggfunc = "sum" , margins = False  , fill_value = 0 ) 

#     t[COL_AMOUNT] = t[COL_AMOUNT].astype(float)
#     meanValue = t[COL_AMOUNT].mean()
#     totalValue = t[COL_AMOUNT].sum()

#     print("Summary --> monthly Mean {:,.2f} , Total {:,.2f} \n\n".format(meanValue , totalValue))

#     t = t.reset_index(drop = False, names = colIndex)    

#     for i in t.index:
#         t.loc[i, 'Delta_from_Mean'] = meanValue - t.loc[i,COL_AMOUNT]

#         if i == 0:
#             t.loc[i, 'Delta'] = 0
#         else:
#             diff_amount = t.loc[i,COL_AMOUNT] - t.loc[i-1 ,COL_AMOUNT ]
#             t.loc[i, 'Delta'] = diff_amount
            
#     t.loc[i+1, colIndex] = 'Total'
#     t.loc[i+1, COL_AMOUNT] = totalValue


#     t.fillna(value=0 , inplace=True)
#     # t[COL_AMOUNT] = t[COL_AMOUNT].apply('{:,.2f}'.format)
#     # t['Delta'] = t['Delta'].apply('{:,.2f}'.format)
#     # t['Delta_from_Mean'] = t['Delta_from_Mean'].apply('{:,.2f}'.format)

#     print(t)
#     print("----------------------------------------")



def expByWeek(dfCsv):

    print("\n\n----------------------------------------")
    print("Expenses (minus recurring and EMI) by Week are as below:")

    # ###################################
    # # removing recurring and EMI expenses
    # dfCsv = dfCsv[ ~dfCsv['Category'].isin(LIST_MONTHLY) ]
    # dfCsv= dfCsv[ ~dfCsv['Category'].isin(LIST_EXCLUDE) ]  

    colIndex = 'WeekNum'
    t = dfCsv.pivot_table(index = colIndex , values = COL_AMOUNT 
                          , aggfunc = "sum" , margins = False  , fill_value = 0 ) 
    t[COL_AMOUNT] = t[COL_AMOUNT].astype(float)
    meanValue = t[COL_AMOUNT].mean()
    totalValue = t[COL_AMOUNT].sum()

    print("Summary --> Weekly Mean {:,.2f} , Monthly Mean {:,.2f}  , Total {:,.2f} \n".format(meanValue , meanValue * 4.33 , totalValue))

    t = t.reset_index(drop = False, names = [colIndex])    

    for i in t.index:
        t.loc[i, 'Delta_from_Mean'] = ( meanValue - t.loc[i,COL_AMOUNT] )

        if i > 0:
            diff_amount = t.loc[i,COL_AMOUNT] - t.loc[i-1 ,COL_AMOUNT ]
            t.loc[i, 'Delta'] = diff_amount
            
    # # print(t)
    # t.loc[i+1, colIndex] = 'Total'
    # t.loc[i+1, COL_AMOUNT] = totalValue

    t.fillna(value=0 , inplace=True)
    # t[COL_AMOUNT] = t[COL_AMOUNT].apply('{:,.2f}'.format)
    # t['Delta'] = t['Delta'].apply('{:,.2f}'.format)
    # t['Delta_from_Mean'] = t['Delta_from_Mean'].apply('{:,.2f}'.format)

    # print(t.to_string(index=False))
    # print("----------------------------------------")
    print(tabulate(t, headers='keys', tablefmt='outline', showindex=False, floatfmt=',.2f', numalign="right"))


def expByWeekday(dfCsv):

    print("\n\n----------------------------------------")
    print("Expenses (minus recurring adn EMI) by WeekDay are as below:")

    # ###################################
    # # removing recurring and EMI expenses
    # dfCsv = dfCsv[ ~dfCsv['Category'].isin(LIST_MONTHLY) ]
    # dfCsv= dfCsv[ ~dfCsv['Category'].isin(LIST_EXCLUDE) ]  

    colIndex = 'Weekday'
    
    # df['Day_Number'] = df['Weekday'].map(weekday_mapping)
    # df = df.set_index(range(1, 4), drop=True)    
    
    t = dfCsv.pivot_table(index = colIndex , values = COL_AMOUNT 
                          , aggfunc = "sum" , margins = False , fill_value = 0 ) 

    t[COL_AMOUNT] = t[COL_AMOUNT].astype(float)
    meanValue = t[COL_AMOUNT].mean()
    totalValue = t[COL_AMOUNT].sum()

    print("Summary --> WeekDay Mean {:,.2f} , Total {:,.2f} \n".format(meanValue , totalValue))

    t = t.reset_index(drop = False, names = [colIndex])    

    x = t[colIndex].map(weekday_mapping)
    t = t.set_index(x, drop=True).sort_index()

    for i in t.index:
        t.loc[i, 'Delta_from_Mean'] = meanValue - t.loc[i,COL_AMOUNT]

        if i > 1:
            diff_amount = t.loc[i,COL_AMOUNT] - t.loc[i-1 ,COL_AMOUNT ]
            t.loc[i, 'Delta'] = diff_amount
            
    # t.loc[i+1, colIndex] = 'Total'
    # t.loc[i+1, COL_AMOUNT] = totalValue

    t.fillna(value=0 , inplace=True)
    # t[COL_AMOUNT] = t[COL_AMOUNT].apply('{:,.2f}'.format)
    # t['Delta'] = t['Delta'].apply('{:,.2f}'.format)
    # t['Delta_from_Mean'] = t['Delta_from_Mean'].apply('{:,.2f}'.format)



    # print(t.to_string(index=False))
    # print("----------------------------------------")
    print(tabulate(t, headers='keys', tablefmt='outline', showindex=False, floatfmt=',.2f', numalign="right"))

    if flagPlot:
        pltX = colIndex
        pltY = COL_AMOUNT
        g = t[t[colIndex] != "Total"]
        g.plot(x=pltX , y=pltY , kind='pie')
        plt.title("Expense per weekday")
        plt.xlabel('Weekday')
        plt.ylabel("Amount in Rs")
        plt.show()     



    
def processForXls(dfFull):
    """
    Processes the full DataFrame to generate various summaries and outputs
    formatted for pasting into an Excel/spreadsheet application.

    Args:
        dfFull (pd.DataFrame): The complete DataFrame with all transactions.
    """
    if flagDebug:
        print("{}processing for XLS".format(zFlow))

    print_in_box("daily income expenses for all file/months as below:", "RED")

    # Separate DataFrame into Income and Expense.
    dfInc = dfFull[ dfFull['Type'] == 'Income' ]
    dfExp = dfFull[ dfFull['Type'] == 'Expense' ].copy()
    dfExp[COL_AMOUNT] = dfExp[COL_AMOUNT] * -1    

    # Isolate monthly recurring expenses and large/excluded expenses.
    dfMonthly = dfExp[ dfExp['Category'].isin(LIST_MONTHLY) ]
    dfExclude= dfExp[ dfExp['Category'].isin(LIST_EXCLUDE) ]
    
    
    # print("Monthly/Recurring numbers are as below:")
    # colIndex = 'YearMonth'
    # t1 = pd.DataFrame()
    # t1 = dfMonthly.pivot_table(index = colIndex , values = COL_AMOUNT 
    #                       , aggfunc = "sum" , margins = False  , fill_value = 0 ) 
    # print(t1)
    # print("----------------------------------------")


    # print("----------------------------------------")
    # print("Monthly large/EMI/excluded numbers are as below:")
    # colIndex = 'YearMonth'
    # t2 = pd.DataFrame()
    # t2 = dfExclude.pivot_table(index = colIndex , values = COL_AMOUNT 
    #                       , aggfunc = "sum" , margins = False  , fill_value = 0 ) 
    # print(t2)
    # print("----------------------------------------")


    # Print details of recurring expenses for each month.
    print(f"Recurring expense details")
    for year_month, group in dfMonthly.groupby('YearMonth'):
        group = group[LIST_SHORT_DISPLAY]
        t1_xls = group
        print(f"\n{year_month}")  # Print YearMonth as header
        # print(group[[COL_AMOUNT , 'Title']].sort_values('Title').to_string(index=False)) 
        print(group.sort_values('Title').to_string(index=False))  
    

    # Print details of large/excluded expenses for each month.
    print(f"\n\nlarge expense details")
    for year_month, group in dfExclude.groupby('YearMonth'):
        t2_xls = group[LIST_SHORT_DISPLAY]         
        print(f"\n{year_month}")  # Print YearMonth as header
        print(t2_xls.sort_values('Title').to_string(index=False))  # Print Title and Amount under the header
    
    print("----------------------------------------")


    # Create a DataFrame for expenses excluding monthly and other excluded categories.
    dfExpLesser = pd.DataFrame()
    dfExpLesser = dfExp[ ~dfExp['Category'].isin(LIST_MONTHLY) ]
    dfExpLesser= dfExpLesser[ ~dfExpLesser['Category'].isin(LIST_EXCLUDE) ]    

    print("Weekend numbers are as below:")
    # Pivot to show weekend expenses aggregated by YearMonth and WeekNum.
    colIndex = LIST_GROUP_BY
    dfWeekend = dfExpLesser[ dfExpLesser['Weekend'] == 'WeekEnd' ]

    t3 = pd.DataFrame()
    t3 = dfWeekend.pivot_table(index = colIndex , values = COL_AMOUNT 
                          , aggfunc = "sum" , margins = False  , fill_value = 0 ) 
    print(t3)
    print("----------------------------------------")


    # print("*******************")







    print("\n\n\n\n\n")
    # print("=============================================")
    print_in_box("daily income expenses for XLS file for last month as below:", "RED")
    # print("=============================================")

    # Output data in CSV format to stdout for easy copy-pasting.
    print(f"\nRecurring and large expenses: ")
    print("-----------------------")
    t1_xls.to_csv(sys.stdout, sep=',', index=False, header=False)
    # print(f"\nlarge/EMI expenses: ")
    print("\n\n\n")
    t2_xls.to_csv(sys.stdout, sep=',', index=False, header=False)
    print("-----------------------")

    # Get the most recent month's data for weekend expenses.
    x = dfFull['YearMonth'].sort_values(ascending=False).unique()    
    lastYearMonth = x[0]

    print(f"\nWeekend expenses: ")
    print("-----------------------")
    t3_xls = dfWeekend[dfWeekend['YearMonth'] == lastYearMonth]
    t3_res = t3_xls.groupby('WeekNum')[COL_AMOUNT].sum()
    t3_res.to_frame().T.to_csv(sys.stdout, sep=',', index=False, header=False)

    # Filter income and remaining expenses for the last month.
    dfInc2 = dfInc[LIST_GROUP_BY + LIST_DISPLAY].sort_values(by='Date', ascending=True) 
    dfExp2 = dfExpLesser[LIST_GROUP_BY + LIST_DISPLAY].sort_values(by='Date', ascending=True) 

    dfInc2 = dfInc2[dfInc2['YearMonth'] == lastYearMonth]
    dfExp2 = dfExp2[dfExp2['YearMonth'] == lastYearMonth] 

    # Format date and print grouped transactions.
    dfInc2['Date'] = dfInc2['Date'].dt.date
    dfExp2['Date'] = dfExp2['Date'].dt.date

    for df in dfInc2, dfExp2:
        print("+++++++++++++")
        for  iWeek , group in df.groupby(LIST_GROUP_BY):
            print(f" ")
            group = group[LIST_DISPLAY]
            # print(group.to_string(index=False , header=False))
            group.to_csv(sys.stdout, sep=',', index=False, header=False)


    # print(dfInc2.to_string(index=False))
    # print("\n\n\n ")
    # print(dfExp2.to_string(index=False))
    print("----------------------------------------")


 



def expMonthPivot(dfCsv):
    
    print("\n\n----------------------------------------")

    t = dfCsv.pivot_table(index = 'Account' , columns = 'YearMonth' , values = COL_AMOUNT ,
                          aggfunc = "sum" , margins = True  , fill_value = 0 )
    for c in t.columns:
        t[c].astype('float64')
        t[c] = t[c].apply('{:,.2f}'.format)   

    print(t)
    print("----------------------------------------")



    t = dfCsv.pivot_table(index = 'Category' , columns = "YearMonth" , values = COL_AMOUNT  ,
                          aggfunc =  "sum", margins = True , 
                          margins_name = COL_TOTAL , fill_value = 0  )
    
    for c in t.columns:
        t[c].astype('float64')
        t[c] = t[c].apply('{:,.2f}'.format)   

    print(t)
    print("----------------------------------------")
    

    t = dfCsv.pivot_table(index = 'Category Group Name' , columns = "YearMonth" , values = COL_AMOUNT , 
                          aggfunc = "sum" , margins = True , 
                          margins_name = COL_TOTAL , fill_value = 0 )
    for c in t.columns:
        t[c].astype('float64')
        # t[c] = t[c].apply('{:,.2f}'.format)   

    print(t)
    print("----------------------------------------")
    

    if flagPlot:
        pltX = 'Category Group Name'
        pltY = "Total"
        t = t.reset_index(drop = False, names = pltX)    
        g = t[[ pltX, pltY]]
        g[pltY] = g[pltY].astype(float)

        g.plot(x=pltX , y=pltY , kind='pie')
        plt.title("Category group total")
        plt.xlabel(pltX)
        plt.ylabel(pltY)
        plt.show() 



def  plotDf(dfCsv):
    if flagDebug:
        print("{}plotting part".format(zFlow))

    # %matplotlib inline
    plt.figure(figsize=(10,8))
    ax = dfCsv.plot(xticks = dfCsv.index , ylabel = 'Amounts', kind = 'bar')
    dfCsv.plot(x = 'Category' , ax = ax , kind = 'bar')
    plt.show()    



def processDf(dfCsv: pd.DataFrame) -> pd.DataFrame:
    """
    Processes the raw DataFrame by cleaning, filtering, and adding new time-based features.

    Args:
        dfCsv (pd.DataFrame): The raw DataFrame loaded from CSV files.

    Returns:
        pd.DataFrame: The processed DataFrame with added features and filtered data.
    """
    if flagFlow:
        print("{}processing CSV DF".format(zFlow))

    
    # Remove 'Transfer' type transactions as they are typically not considered income or expense.
    dfCsv = dfCsv[ dfCsv['Type'] != 'Transfer' ] 

    # Calculate the start date for filtering transactions.
    # It takes `daysInPast` into account and sets the start to the first day of that month.
    today = date.today()
    prevDate = today - timedelta(days=daysInPast)
    startDate = prevDate.replace(day=1)
    startDate = pd.to_datetime(startDate)
    
    # dfCsv['Date'] = dfCsv['Date'].astype('date')  # Ensure Date is in datetime format
    # dfCsv['Date'] = pd.to_datetime(dfCsv['Date'])

    # this to handle changes in app csv export
    dfCsv['Date'] = dfCsv['Date'].str[:19]
    dfCsv['Date'] = pd.to_datetime(dfCsv['Date'])
    
    # Filter out transactions older than the calculated startDate.
    dfCsv = dfCsv[dfCsv["Date"] >= startDate ]
    if dfCsv.empty:
        print(f"No data found for date greater than {startDate}")
        return None 
        # sys.exit(0)

    # print(dfCsv['Date'])



    # Add new time-based features to the DataFrame.
    # Efficient Approach
    dfCsv["Weekday"] = dfCsv["Date"].dt.day_name()
    dfCsv["YearMonth"] = dfCsv["Date"].dt.strftime("%Y-%m")
    # dfCsv["Weekday"] = dfCsv.apply(lambda x : x.Date.strftime("%A")  , axis = 1)
    # dfCsv["YearMonth"] = dfCsv.apply(lambda x : x.Date.strftime("%Y-%m")  , axis = 1)
    
    dfCsv["Weekend"] = dfCsv.apply(lambda x :  'WeekEnd' if x["Weekday"] in ('Saturday','Sunday') else 'WeekDay' , axis = 1)
    # dfCsv["WeekNum"] = dfCsv.apply(lambda x : x.Date.strftime("%Y-%U")  , axis = 1)
    dfCsv["WeekNum"] = dfCsv["Date"].dt.isocalendar().week
    dfCsv["WeekNum"] = dfCsv["WeekNum"].astype(str)
    # dfCsv["YearWeek"] = dfCsv["Date"].dt.isocalendar().year.astype(str) + "-" + dfCsv["WeekNum"].astype(str).str.zfill(2)
    # print(dfCsv.columns )

    # Fill any missing 'Amount' values with 0.
    dfCsv["Amount"].fillna(0 , inplace = True)
    # dfCsv["Amount"] = dfCsv.apply(lambda row : (row["Amount"] * -1) if row["Type"] == 'Expense' else row["Amount"] , axis = 1 )

    # Rename the 'Amount' column to the standardized `COL_AMOUNT`.
    dfCsv.rename(columns = {'Amount': COL_AMOUNT} , inplace = True)

    
    return dfCsv
    
    



def getFiles():
    if flagFlow:
        print("{}finding files ".format(zFlow))

    for root, dirnames, filenames in os.walk(filePath):        
        for fileFound in fnmatch.filter(filenames, fileName):
            yield os.path.join(root, fileFound)    


def main():

    if flagFlow:
        print("{}starting main".format(zFlow))

    # Check if the filePath directory exists
    if not os.path.isdir(filePath):
        print(f"Error: Directory '{filePath}' not found. Please check the 'filePath' in config.ini.")
        sys.exit(1)


    dfFile = pd.DataFrame()


    
    ###########################
    # Look for all files and load them in df
    df_all = []
    for myFile in getFiles():
        if flagDebug:
            print(myFile)

        try:
            dfTmp = pd.read_csv(myFile)    
        except FileNotFoundError as e:
            print(f"missing file  - {e}")            
        except Exception as e:
            print(f"generic error -- {e}")
            print(f"Skipping current file {myFile}")

        else:

            # To handle changes in app csv export
            if 'Name' in dfTmp.columns:
                dfTmp.rename(columns={'Name': 'Title'}, inplace=True)

            dfTmp = dfTmp.round(2)
            df_all.append(dfTmp)
            

            if flagDebug:
                print(" file {} got {} rows  ".format(myFile , dfTmp.shape[0]  ))
            
    if not df_all:
        print(f"No files found matching {fileName} in {filePath}")
        sys.exit(1)
    
    dfFile = pd.concat(df_all, ignore_index=True)

    # # Check and flag duplicates
    # if dfFile.duplicated().any():
    #     print(f"Warning: Found {dfFile.duplicated().sum()} duplicate rows.")
    #     # Flag duplicates in a new column for further inspection
    #     dfFile['is_duplicate'] = dfFile.duplicated(keep=False)

    if flagDebug:
        print("Total rows are {}".format( dfFile.shape[0]  ))


    if dfFile.empty:
        print("No data found in file {}".format(fileName))
        sys.exit(1)
    else:
        dfFile['Labels'] = dfFile['Labels'].str.replace(r'(,|^)\s*0\s+', r'\1', regex=True)
        # dfFile['Labels'] = dfFile['Labels'].str.replace(r'^0\s+', r'', regex=True)
        dfFile = processDf(dfFile)
        if dfFile is None:
            print(f"Empty dataset, nothing to process - check for dates or Trans Type")
            sys.exit(2)




    if printForAnalysis:
        ###################
        # checking stuff here
        amountsSummaryByMonth(dfFile)

        dfIncome = dfFile[ dfFile['Type'] == 'Income' ]  
        amtByMonth(dfIncome , "Income")
        
        dfExp = dfFile[ dfFile['Type'] == 'Expense' ]    
        dfExp[COL_AMOUNT] = dfExp[COL_AMOUNT] * -1
        amtByMonth(dfExp , "Expense")    
        

        ###################################
        # removing recurring and EMI expenses    
        dfExcluded = dfExp[ ~dfExp['Category'].isin(LIST_MONTHLY) ]
        dfExcluded= dfExp[ ~dfExp['Category'].isin(LIST_EXCLUDE) ]    

        expByWeekday(dfExcluded)
        expByWeek(dfExcluded)


    if printForXls:
        print("\n\n\n\n----------------------------------------")
        processForXls(dfFile)    
    
    # expMonthPivot(dfCsv)    
       
    # plotDf(dfFile)


    


if __name__ == "__main__":
    main()