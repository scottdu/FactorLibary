# pylint: disable=I0011,C0111, C0103,C0326,C0301, C0304, W0401,W0614
from cassandra.cluster import Cluster
from cassandra.util import Date
import time
import datetime
import csv
import os

################################################################################################
## Select all valid stock with required factors identified by stock code & date, saved in CSV ##
################################################################################################
def export(fileName, beginDate, endDate=datetime.datetime.today().date(), factors = [], table = "factors_month"):
    if len(factors) == 0 or beginDate > endDate or len(fileName) == 0:
        return
    # cassandra connection
    #cluster = Cluster(['192.168.1.111'])
    cluster = Cluster(['202.120.40.111'])
    session = cluster.connect('factors') #connect to the keyspace 'factors'

    # get valid stocks in A share
    rows = session.execute('''select stock from stock_info''')
    stocks = []
    for row in rows:
        stocks.append(row[0])

    # sorting factors since they're ordered in cassandra
    # factors = sorted(factors)
    # print("Sorted factors: ", factors)

    #time list
    rows = session.execute('''
        select * from transaction_time 
        where type='M' and time >= %s and time <= %s ALLOW FILTERING;''', [beginDate, endDate])
    dateList = []
    for row in rows:
        dateList.append(row.time)

    countStmt = session.prepare(''' SELECT count(*) from factors_month WHERE factor = 'close' and time = ? ALLOW FILTERING ; ''')
    # prepare SQL
    SQL = "SELECT * FROM "+table+" WHERE stock = ? AND factor IN ("
    for factor in factors:
        SQL = SQL + "'"+ factor + "',"
    SQL = SQL[:-1]
    SQL = SQL +") AND time = ?;"
    print (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), " PREPARE QUERY SQL: \n"+SQL)
    preparedStmt = session.prepare(SQL)

    # open CSV file & write first line: title
    # NOTICE:  [wb] mode won't result in problem of blank line
    with open(fileName, 'w') as csvFile:
        factors = factors + ['Yield_Rank_Class']
        names = ['id']  + factors # column names
        print (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), " ---- Starting to export ------ \r\n")
        f = csv.writer(csvFile, delimiter=',',lineterminator='\n')
        f.writerow(names)

        # retrieve data
        for day in dateList:
            # real stock number on every trading day
            rows = session.execute(countStmt,(day,))
            for row in rows:
                validStockNum = row[0]
                break
            for stock in stocks:
                line = []
                dic = {}    # paired K/V for ordering
                rows = session.execute(preparedStmt, (stock,day))

                # pass when no data
                empty = True
                line.append(stock+'_' + str(day))
                for row in rows:
                    empty = False
                    if row.factor.find('rank') != -1:
                        rank = int(row.value / validStockNum * 1000) # normalize rank value

                        if row.factor.find('Yield') != -1:
                            # rank = int(row.value / totalStockNum * 1000)
                            ##################################################
                            ####### CODE Area for Yield Rank Classification ##
                            ##################################################
                            # class 1: [1, 26]
                            if rank > 1 * 10 and rank < 26 * 10:
                                #line.append(1)
                                dic['Yield_Rank_Class'] = '1'
                            # class 0: [74, 99]
                            elif rank > 74 * 10 and rank < 99 * 10:
                                #line.append(0)
                                dic['Yield_Rank_Class'] = '0'
                            else:
                                #line.append('') #no class, fill in empty char to keep CSV well-formed
                                dic['Yield_Rank_Class'] = ''
                            # line.append(rank)

                        dic[row.factor] = rank

                    # elif row.factor.find('Yield') != -1:
                    #     # line.append('') # empty for Yield Binary Class
                    #     # line.append(str(row.value))
                    #     dic['Yield_Rank_Class'] = ''
                    #     dic['Yield'] = str(row.value)
                    else:
                        # line.append(str(row.value))
                        dic[row.factor] = row.value
                if empty:
                    continue
                # write row
                # print (dic)
                empty = False
                for factor in factors:
                    try:
                        line.append(dic[factor])
                    except KeyError:
                        # print(" --- Empty Omitted %s 's factor: %s " % (row.stock, factor))
                        empty = True
                        break
                if empty == False:
                    f.writerow(line)
            print (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "  Writing at "+str(day))
    # close connection with cassandra
    cluster.shutdown()
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'Writing to ',fileName,' complete!')

##############################################
################# USAGE EXAMPLE ##############
export('E:\\train.csv', datetime.date(2016,10,1),factors=['mkt_freeshares_rank', 'mmt_rank', 'roa_growth_rank','Yield_rank'])