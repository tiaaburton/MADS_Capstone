import pandas as pd
import pymongo
import configparser

config = configparser.ConfigParser()
config.read('milestone-local.ini')
mongo_config = config['MONGO']
mongo_connection = "mongodb://" + mongo_config['User'] + ":" + mongo_config['Password'] + "@" + mongo_config['Address'] + ":" + mongo_config['port'] + "/?authSource=admin"
myclient = pymongo.MongoClient(mongo_connection)
mydb = myclient["stocks"]
sub_col = mydb["financial_sub"]
num_col = mydb["financial_num"]
tag_col = mydb["financial_tag"]
pre_col = mydb["financial_pre"]
calc_col = mydb["financial_calc"]
comp_col = mydb["financial_comp"]
sec_col = mydb["sec"]
nasdaq_col = mydb["nasdaq"]
sec_ticker_col = mydb["sec_ticker"]
price_col = mydb["stock_price"]
price_yah_col = mydb["stock_price_yahoo"]
config_col = mydb["config"]
analysis_all_col = mydb["analysis_all"]
analysis_underval_col = mydb["analysis_undervalued"]
analysis_fairval_col = mydb["analysis_fairvalued"]

tickers = ['DT', 'MMM', 'AXP', 'AMGN', 'AAPL', 'CAT', 'CVX', 'CSCO', 'DOW', 'HON', 'INTC', 'IBM', 'JNJ', 'JPM', 'MCD', 'MRK', 'MSFT', 'NKE', 'CRM', 'BA', 'KO', 'GS', 'HD', 'PG', 'TRV', 'DIS', 'UNH', 'VZ', 'V', 'WBA', 'WMT', 'A', 'AAL', 'AAP', 'ABC', 'ABMD', 'ABT', 'ACN', 'ADBE', 'ADI', 'ADM', 'ADP', 'ADSK', 'AEE', 'AEP', 'AES', 'AFL', 'AIG', 'AIZ', 'AJG', 'AKAM', 'ALB', 'ALGN', 'ALK', 'ALL', 'ALLE', 'ALXN', 'AMAT', 'AMCR', 'AMD', 'AME', 'AMT', 'AMZN', 'ANET', 'ANSS', 'ANTM', 'AON', 'AOS', 'APA', 'APD', 'APH', 'ARE', 'ATO', 'ATVI', 'AVB', 'AVGO', 'AVY', 'AWK', 'AZO', 'BAC', 'BAX', 'BBY', 'BDX', 'BEN', 'BF.B', 'BIIB', 'BIO', 'BK', 'BKNG', 'BKR', 'BLK', 'BLL', 'BMY', 'BR', 'BRK.B', 'BSX', 'BWA', 'BXP', 'C', 'CAG', 'CAH', 'CARR', 'CB', 'CBOE', 'CBRE', 'CCI', 'CDNS', 'CE', 'CERN', 'CF', 
'CFG', 'CHD', 'CHRW', 'CHTR', 'CI', 'CINF', 'CL', 'CLX', 'CMCSA', 'CME', 'CMG', 'CMI', 'CMS', 'CNC', 'CNP', 'COF', 'COG', 'COO', 'COP', 'COST', 'CPB', 'CPRT', 'CSX', 'CTAS', 'CTLT', 'CTSH', 'CTVA', 
'CTXS', 'CVS', 'D', 'DAL', 'DD', 'DE', 'DFS', 'DG', 'DGX', 'DHI', 'DHR', 'DISCA', 'DISH', 'DLR', 'DLTR', 'DOV', 'DPZ', 'DRE', 'DRI', 'DTE', 'DUK', 'DVA', 'DVN', 'DXC', 'DXCM', 'EA', 'EBAY', 'ECL', 'ED', 'EFX', 'EIX', 'EL', 'EMN', 'EMR', 'EOG', 'EQIX', 'EQR', 'ES', 'ESS', 'ETN', 'ETR', 'ETSY', 'EVRG', 'EW', 'EXC', 'EXPD', 'EXPE', 'EXR', 'F', 'FAST', 'FB', 'FCX', 'FDX', 'FE', 
'FFIV', 'FIS', 'FISV', 'FITB', 'FLIR', 'FLS', 'FLT', 'FMC', 'FOXA', 'FRT', 'FTI', 'FTNT', 'FTV', 'GD', 'GE', 'GILD', 'GIS', 'GL', 'GLW', 'GM', 'GOOGL', 'GPC', 'GPN', 'GPS', 'GRMN', 'HAL', 'HAS', 'HBAN', 'HBI', 'HCA', 'HES', 'HFC', 'HIG', 'HII', 'HLT', 'HOLX', 'HPE', 'HPQ', 'HRL', 'HSIC', 'HST', 'HSY', 'HUM', 'ICE', 'IDXX', 'IEX', 'IFF', 'ILMN', 'INCY', 'INFO', 'INTU', 'IP', 'IPG', 'IPGP', 'IQV', 'IRM', 'ISRG', 'IT', 'ITW', 'J', 'JBHT', 'JCI', 'JKHY', 'JNPR', 'K', 'KEY', 'KEYS', 'KIM', 'KLAC', 'KMB', 'KMI', 'KMX', 'KR', 'KSU', 'L', 'LB', 'LDOS', 'LEG', 'LEN', 'LH', 'LHX', 'LIN', 'LKQ', 'LLY', 'LMT', 'LNC', 'LNT', 'LOW', 'LRCX', 'LUMN', 'LUV', 'LVS', 'LW', 'LYB', 'LYV', 'MA', 'MAA', 'MAR', 'MAS', 'MCHP', 'MCK', 'MCO', 'MDLZ', 'MDT', 'MET', 'MGM', 'MHK', 'MKC', 'MKTX', 'MLM', 'MMC', 'MNST', 'MO', 'MOS', 'MRO', 'MS', 'MSCI', 'MSI', 'MTB', 'MTD', 'MU', 'MXIM', 'NDAQ', 'NEE', 'NEM', 'NFLX', 'NI', 'NLOK', 'NLSN', 'NOC', 'NOV', 'NOW', 'NRG', 'NSC', 'NTAP', 'NTRS', 'NUE', 'NVDA', 'NVR', 'NWL', 'NWSA', 'O', 'ODFL', 'OKE', 'OMC', 'ORCL', 'ORLY', 'OTIS', 'OXY', 'PAYC', 'PAYX', 'PBCT', 'PCAR', 'PEAK', 'PEG', 'PEP', 'PFE', 'PFG', 'PGR', 'PH', 'PHM', 'PKG', 'PKI', 'PLD', 'PM', 'PNC', 'PNR', 'PNW', 'POOL', 'PPG', 'PPL', 'PRGO', 'PRU', 'PSA', 'PVH', 'PWR', 'PXD', 'PYPL', 'QCOM', 'QRVO', 'RCL', 'RE', 'REG', 'REGN', 'RF', 'RHI', 'RJF', 'RL', 'RMD', 'ROK', 'ROL', 'ROP', 'ROST', 'RSG', 'RTX', 'SBAC', 'SBUX', 'SCHW', 'SEE', 'SHW', 'SIVB', 'SJM', 'SLB', 'SLG', 'SNA', 'SNPS', 'SO', 'SPG', 'SPGI', 'SRE', 'STE', 'STT', 'STX', 'STZ', 'SWK', 'SWKS', 'SYF', 
'SYK', 'SYY', 'T', 'TAP', 'TDG', 'TDY', 'TEL', 'TER', 'TFC', 'TFX', 'TGT', 'TJX', 'TMO', 'TMUS', 'TPR', 'TRMB', 'TROW', 'TSCO', 'TSLA', 'TSN', 'TT', 'TTWO', 'TWTR', 'TXN', 'TXT', 'TYL', 'UAA', 'UAL', 'UDR', 'UHS', 'ULTA', 'UNM', 'UNP', 'UPS', 'URI', 'USB', 'VAR', 'VFC', 'VIAC', 'VLO', 'VMC', 'VNO', 'VNT', 'VRSK', 'VRSN', 'VRTX', 'VTR', 'VTRS', 'WAB', 'WAT', 'WDC', 'WEC', 'WELL', 'WFC', 'WHR', 'WLTW', 
'WM', 'WMB', 'WRB', 'WRK', 'WST', 'WU', 'WY', 'WYNN', 'XEL', 'XLNX', 'XOM', 'XRAY', 'XRX', 'YUM', 'ZBH', 'ZBRA', 'ZION']
ciks = [1773383, 12927, 320193, 320187, 310158, 80424, 1403161, 789019, 858877, 1744489, 732712, 19617, 886982, 354950, 104169, 731766, 773840, 200406, 63908, 4962, 66740, 21344, 86312, 18230, 51143, 1618921, 93410, 1751788, 50863, 1108524, 318154, 1800, 2488, 2969, 4127, 4281, 4447, 4904, 4977, 5272, 5513, 6201, 6281, 6769, 6951, 7084, 8670, 8818, 9389, 10456, 10795, 11544, 12208, 14272, 14693, 16732, 16918, 18926, 20286, 21076, 21665, 23217, 24545, 24741, 26172, 27419, 27904, 28412, 29534, 29905, 29989, 30625, 31462, 31791, 32604, 33185, 34088, 34903, 35527, 36104, 36270, 37785, 37996, 38777, 39911, 40533, 40545, 40704, 40987, 45012, 46080, 47111, 47217, 48039, 48465, 49071, 49196, 49826, 51253, 51434, 51644, 52988, 54480, 55067, 55785, 56873, 58492, 59478, 59558, 60086, 60667, 62709, 62996, 63754, 64040, 64803, 65984, 68505, 70858, 72741, 72903, 72971, 73124, 73309, 74208, 75362, 75677, 76334, 77360, 77476, 78003, 78239, 79879, 80661, 84839, 87347, 89800, 91142, 91419, 91440, 91576, 92122, 92230, 92380, 93556, 93751, 96021, 96943, 97210, 97476, 97745, 100493, 100517, 100885, 101778, 101829, 103379, 105770, 106040, 106535, 106640, 107263, 109198, 109380, 202058, 203527, 217346, 277135, 277948, 310764, 313616, 313927, 315189, 315213, 315293, 316709, 319201, 320335, 352541, 352915, 354190, 354908, 701985, 702165, 707549, 711404, 712515, 713676, 715957, 718877, 719739, 720005, 721371, 723125, 723254, 723531, 726728, 728535, 731802, 732717, 740260, 743316, 743988, 745732, 746515, 749251, 753308, 759944, 764180, 764478, 764622, 765880, 766421, 766704, 769397, 779152, 783280, 783325, 788784, 789570, 796343, 797468, 798354, 
804328, 804753, 811156, 813672, 813828, 814453, 815094, 815097, 815556, 818479, 820027, 820313, 821189, 822416, 823768, 827052, 827054, 829224, 831001, 831259, 832101, 833444, 849399, 851968, 858470, 859737, 860730, 860731, 864749, 865752, 866787, 872589, 874716, 874761, 874766, 875045, 875320, 877212, 877890, 878927, 879101, 879169, 882095, 882184, 882835, 883241, 884887, 885725, 895421, 896159, 896878, 898173, 899051, 899689, 899866, 900075, 906107, 906163, 908255, 909832, 910606, 912595, 914208, 915389, 915912, 915913, 916076, 916365, 920148, 920522, 920760, 922224, 927066, 927628, 927653, 935703, 936340, 936468, 940944, 943452, 943819, 945841, 946581, 1000228, 1000697, 1001082, 1001250, 1002047, 1002910, 1012100, 1013462, 1013871, 1014473, 1018724, 1020569, 1021860, 1022079, 1024478, 1031296, 1032208, 1034054, 1035002, 1035267, 1035443, 1037038, 1037540, 1037646, 1037868, 1038357, 1039684, 1040971, 1041061, 1043277, 1043604, 1045609, 1045810, 1047862, 1048286, 1048695, 1048911, 1050915, 1051470, 1053507, 1058090, 1058290, 1059556, 1060391, 1063761, 1065088, 1065280, 1065696, 1067701, 1067983, 1070750, 1071739, 1075531, 1086222, 1090012, 1090727, 1090872, 1091667, 1093557, 1094285, 1095073, 1097149, 1099219, 1099800, 1101239, 1103982, 1109357, 1110803, 1111711, 1111928, 1113169, 1116132, 1120193, 1121788, 1123360, 1126328, 1130310, 1132979, 1133421, 1136869, 1136893, 1137774, 1137789, 1138118, 1140536, 1140859, 1141391, 1156039, 1156375, 1158449, 1163165, 1164727, 1166691, 1170010, 1174922, 1175454, 1260221, 1262039, 1267238, 1278021, 1281761, 1283699, 1285785, 1286681, 1289490, 1297996, 1300514, 1306830, 1318605, 1324404, 1324424, 1326160, 1326801, 1335258, 1336917, 1336920, 1341439, 1359841, 1364742, 1365135, 1370637, 1373715, 1374310, 1378946, 1383312, 1385157, 1390777, 1393311, 1393612, 1396009, 1402057, 1403568, 1408198, 1410636, 1413329, 1418091, 1437107, 1442145, 1463101, 1466258, 1467373, 1467858, 1478242, 1489393, 1492633, 1501585, 1506307, 1510295, 1513761, 1519751, 1521332, 1524472, 1534701, 1539838, 
1551152, 1551182, 1555280, 1564708, 1571949, 1579241, 1585364, 1585689, 1590955, 1596532, 1596783, 1598014, 1601046, 1601712, 1604778, 1613103, 1633917, 1637459, 1645590, 1652044, 1659166, 1666700, 1679273, 1681459, 1688568, 1699150, 1701605, 1707925, 1711269, 1730168, 1732845, 1739940, 1748790, 1754301, 1755672, 1757898, 1770450, 1781335, 1783180, 1786842, 1792044]
ciks_dow = [1773383, 12927, 320193, 320187, 310158, 80424,  1403161, 789019,  858877, 1744489, 732712,  19617, 886982, 354950,  104169,  731766,  773840, 200406, 63908, 4962, 66740, 21344, 86312, 18230, 51143, 1618921, 93410, 1751788, 50863, 1108524, 318154]
ticker_cik = {'DT': 1773383, 'BA': 12927, 'AAPL': 320193, 'NKE': 320187, 'MRK': 310158, 'PG': 80424, 'V': 1403161, 'MSFT': 789019, 'CSCO': 858877, 'DIS': 1744489, 'VZ': 732712, 'JPM': 19617, 'GS': 886982, 'HD': 354950, 'WMT': 104169, 'UNH': 731766, 'HON': 773840, 'JNJ': 200406, 'MCD': 63908, 'AXP': 4962, 'MMM': 66740, 'KO': 21344, 'TRV': 86312, 'CAT': 18230, 'IBM': 51143, 'WBA': 1618921, 'CVX': 93410, 'DOW': 1751788, 'INTC': 50863, 'CRM': 1108524, 'AMGN': 318154, 'A': 1090872, 'AAL': 6201, 'AAP': 1158449, 'ABBV': 1551152, 'ABC': 1140859, 'ABMD': 815094, 'ABT': 1800, 'ACN': 1467373, 'ADBE': 796343, 'ADI': 6281, 'ADM': 7084, 'ADP': 8670, 'ADSK': 769397, 'AEE': 1002910, 'AEP': 4904, 'AES': 874761, 'AFL': 4977, 'AIG': 5272, 'AIZ': 1267238, 'AJG': 354190, 'AKAM': 1086222, 'ALB': 915913, 'ALGN': 1097149, 'ALK': 766421, 'ALL': 899051, 'ALLE': 1579241, 'ALXN': 899866, 'AMAT': 6951, 'AMCR': 1748790, 'AMD': 2488, 'AME': 1037868, 'AMP': 820027, 'AMT': 1053507, 'AMZN': 1018724, 'ANET': 1596532, 'ANSS': 1013462, 'ANTM': 1156039, 'AON': 315293, 'AOS': 91142, 'APA': 6769, 'APD': 2969, 'APH': 820313, 'APTV': 1521332, 'ARE': 1035443, 'ATO': 731802, 'ATVI': 718877, 'AVB': 915912, 'AVGO': 1730168, 'AVY': 8818, 'AWK': 1410636, 'AZO': 866787, 'BAC': 70858, 'BAX': 10456, 'BBY': 764478, 'BDX': 10795, 'BEN': 38777, 'BF.B': 14693, 'BIIB': 875045, 'BIO': 12208, 'BK': 1390777, 'BKNG': 1075531, 'BKR': 1701605, 'BLK': 1364742, 'BLL': 9389, 'BMY': 14272, 'BR': 1383312, 'BRK.B': 1067983, 'BSX': 885725, 'BWA': 908255, 'BXP': 1037540, 'C': 831001, 'CAG': 23217, 'CAH': 721371, 'CARR': 1783180, 'CB': 896159, 'CBOE': 1374310, 'CBRE': 1138118, 'CCI': 1051470, 'CCL': 815097, 'CDNS': 813672, 'CDW': 1402057, 'CE': 1306830, 'CERN': 804753, 'CF': 1324404, 'CFG': 759944, 'CHD': 313927, 'CHRW': 1043277, 'CHTR': 1091667, 'CI': 1739940, 'CINF': 20286, 'CL': 21665, 'CLX': 
21076, 'CMA': 28412, 'CMCSA': 1166691, 'CME': 1156375, 'CMG': 1058090, 'CMI': 26172, 'CMS': 811156, 'CNC': 1071739, 'CNP': 1130310, 'COF': 927628, 'COG': 858470, 'COO': 711404, 'COP': 1163165, 'COST': 909832, 'CPB': 16732, 'CPRT': 900075, 'CSX': 277948, 'CTAS': 723254, 'CTLT': 1596783, 'CTSH': 1058290, 'CTVA': 1755672, 'CTXS': 877890, 'CVS': 64803, 'D': 715957, 'DAL': 27904, 'DD': 1666700, 'DE': 315189, 'DFS': 1393612, 'DG': 29534, 'DGX': 1022079, 'DHI': 882184, 'DHR': 313616, 'DISCA': 1437107, 'DISCK': 1437107, 'DISH': 1001082, 'DLR': 1297996, 'DLTR': 935703, 'DOV': 29905, 'DPZ': 1286681, 'DRE': 783280, 'DRI': 940944, 'DTE': 936340, 'DUK': 1326160, 'DVA': 927066, 'DVN': 1090012, 'DXC': 1688568, 'DXCM': 1093557, 'EA': 712515, 'EBAY': 1065088, 'ECL': 31462, 'ED': 1047862, 'EFX': 33185, 'EIX': 827052, 'EL': 1001250, 'EMN': 915389, 'EMR': 32604, 'ENPH': 1463101, 'EOG': 821189, 'EQIX': 1101239, 'EQR': 906107, 'ES': 72741, 'ESS': 920522, 'ETN': 1551182, 'ETR': 65984, 'ETSY': 1370637, 'EVRG': 1711269, 'EW': 1099800, 'EXC': 1109357, 'EXPD': 746515, 'EXPE': 1324424, 'EXR': 1289490, 'F': 37996, 'FANG': 1539838, 'FAST': 815556, 'FB': 1326801, 'FBHS': 1519751, 'FCX': 831259, 'FDX': 1048911, 'FE': 1031296, 'FFIV': 1048695, 'FIS': 1136893, 'FISV': 798354, 'FITB': 35527, 'FLIR': 354908, 'FLS': 30625, 'FLT': 1175454, 'FMC': 37785, 'FOX': 1754301, 'FOXA': 1754301, 'FRC': 1132979, 'FRT': 34903, 'FTI': 1681459, 'FTNT': 1262039, 'FTV': 1659166, 'GD': 40533, 'GE': 40545, 'GILD': 882095, 'GIS': 40704, 'GL': 320335, 'GLW': 24741, 'GM': 1467858, 'GOOG': 1652044, 'GOOGL': 1652044, 'GPC': 40987, 'GPN': 1123360, 'GPS': 39911, 'GRMN': 1121788, 'GWW': 277135, 'HAL': 45012, 'HAS': 46080, 'HBAN': 49196, 'HBI': 1359841, 'HCA': 860730, 'HES': 4447, 'HFC': 48039, 'HIG': 874766, 'HII': 1501585, 'HLT': 1585689, 'HOLX': 859737, 'HPE': 1645590, 'HPQ': 47217, 'HRL': 48465, 'HSIC': 1000228, 'HST': 1070750, 'HSY': 47111, 'HUM': 49071, 'HWM': 4281, 'ICE': 1571949, 'IDXX': 874716, 'IEX': 832101, 'IFF': 51253, 'ILMN': 1110803, 'INCY': 879169, 'INFO': 1598014, 'INTU': 896878, 'IP': 51434, 'IPG': 51644, 'IPGP': 1111928, 'IQV': 1478242, 'IR': 1699150, 'IRM': 1020569, 'ISRG': 1035267, 'IT': 749251, 'ITW': 49826, 'IVZ': 914208, 'J': 52988, 'JBHT': 728535, 'JCI': 
833444, 'JKHY': 779152, 'JNPR': 1043604, 'K': 55067, 'KEY': 91576, 'KEYS': 1601046, 'KHC': 1637459, 'KIM': 879101, 'KLAC': 319201, 'KMB': 55785, 'KMI': 1506307, 'KMX': 1170010, 'KR': 56873, 'KSU': 54480, 'L': 60086, 'LB': 701985, 'LDOS': 1336920, 'LEG': 58492, 'LEN': 920760, 'LH': 920148, 'LHX': 202058, 'LIN': 1707925, 'LKQ': 1065696, 'LLY': 59478, 'LMT': 936468, 'LNC': 59558, 'LNT': 352541, 'LOW': 60667, 'LRCX': 707549, 'LUMN': 18926, 'LUV': 92380, 'LVS': 1300514, 'LW': 1679273, 'LYB': 1489393, 'LYV': 1335258, 'MA': 1141391, 'MAA': 912595, 'MAR': 1048286, 'MAS': 62996, 'MCHP': 827054, 'MCK': 927653, 'MCO': 
1059556, 'MDLZ': 1103982, 'MDT': 1613103, 'MET': 1099219, 'MGM': 789570, 'MHK': 851968, 'MKC': 63754, 'MKTX': 1278021, 'MLM': 916076, 'MMC': 62709, 'MNST': 865752, 'MO': 764180, 'MOS': 1285785, 'MPC': 1510295, 'MRO': 101778, 'MS': 895421, 'MSCI': 1408198, 'MSI': 68505, 'MTB': 36270, 'MTD': 1037646, 'MU': 723125, 'MXIM': 743316, 'NCLH': 1513761, 'NDAQ': 1120193, 'NEE': 753308, 'NEM': 1164727, 'NFLX': 1065280, 'NI': 1111711, 'NLOK': 849399, 'NLSN': 1492633, 'NOC': 1133421, 'NOV': 1021860, 'NOW': 1373715, 'NRG': 1013871, 'NSC': 702165, 'NTAP': 1002047, 'NTRS': 73124, 'NUE': 73309, 'NVDA': 1045810, 'NVR': 906163, 'NWL': 814453, 'NWS': 1564708, 'NWSA': 1564708, 'O': 726728, 'ODFL': 878927, 'OKE': 1039684, 'OMC': 29989, 'ORCL': 1341439, 'ORLY': 898173, 'OTIS': 1781335, 'OXY': 797468, 'PAYC': 1590955, 'PAYX': 723531, 'PBCT': 1378946, 'PCAR': 75362, 'PEAK': 765880, 'PEG': 788784, 'PEP': 77476, 'PFE': 78003, 'PFG': 1126328, 'PGR': 80661, 'PH': 76334, 'PHM': 822416, 'PKG': 75677, 'PKI': 31791, 'PLD': 1045609, 'PM': 1413329, 'PNC': 713676, 'PNR': 77360, 'PNW': 764622, 'POOL': 945841, 'PPG': 79879, 'PPL': 922224, 'PRGO': 1585364, 'PRU': 1137774, 'PSA': 1393311, 'PSX': 1534701, 'PVH': 78239, 'PWR': 1050915, 'PXD': 1038357, 
'PYPL': 1633917, 'QCOM': 804328, 'QRVO': 1604778, 'RCL': 884887, 'RE': 1095073, 'REG': 910606, 'REGN': 872589, 'RF': 1281761, 'RHI': 315213, 'RJF': 720005, 'RL': 1037038, 'RMD': 943819, 'ROK': 1024478, 'ROL': 84839, 'ROP': 882835, 'ROST': 745732, 'RSG': 1060391, 'RTX': 101829, 'SBAC': 1034054, 'SBUX': 829224, 'SCHW': 316709, 'SEE': 1012100, 'SHW': 89800, 'SIVB': 719739, 'SJM': 91419, 'SLB': 87347, 'SLG': 1040971, 'SNA': 91440, 'SNPS': 883241, 'SO': 92122, 'SPG': 1063761, 'SPGI': 64040, 'SRE': 1032208, 'STE': 1757898, 'STT': 93751, 'STX': 1137789, 'STZ': 16918, 'SWK': 93556, 'SWKS': 4127, 'SYF': 1601712, 'SYK': 310764, 'SYY': 96021, 'T': 732717, 'TAP': 24545, 'TDG': 1260221, 'TDY': 1094285, 'TEL': 1385157, 'TER': 97210, 'TFC': 92230, 'TFX': 96943, 'TGT': 27419, 'TJX': 109198, 'TMO': 97745, 'TMUS': 1283699, 'TPR': 1116132, 'TRMB': 864749, 'TROW': 1113169, 'TSCO': 916365, 'TSLA': 1318605, 'TSN': 100493, 'TT': 1466258, 'TTWO': 946581, 'TWTR': 1418091, 'TXN': 97476, 'TXT': 217346, 'TYL': 860731, 'UA': 1336917, 'UAA': 1336917, 'UAL': 100517, 'UDR': 74208, 'UHS': 352915, 'ULTA': 1403568, 'UNM': 5513, 'UNP': 100885, 'UPS': 1090727, 'URI': 1067701, 'USB': 36104, 'VAR': 203527, 'VFC': 103379, 'VIAC': 813828, 'VLO': 1035002, 'VMC': 1396009, 'VNO': 899689, 'VNT': 1786842, 'VRSK': 1442145, 'VRSN': 1014473, 'VRTX': 875320, 'VTR': 740260, 'VTRS': 1792044, 'WAB': 943452, 'WAT': 1000697, 'WDC': 106040, 'WEC': 783325, 'WELL': 766704, 'WFC': 72971, 'WHR': 106640, 'WLTW': 1140536, 'WM': 823768, 'WMB': 107263, 'WRB': 11544, 'WRK': 1732845, 'WST': 105770, 'WU': 1365135, 'WY': 106535, 'WYNN': 1174922, 'XEL': 72903, 'XLNX': 743988, 'XOM': 34088, 'XRAY': 818479, 'XRX': 1770450, 'XYL': 1524472, 'YUM': 1041061, 'ZBH': 1136869, 'ZBRA': 877212, 'ZION': 109380, 'ZTS': 1555280}
cik_ticker = {1800: 'ABT', 2488: 'AMD', 2969: 'APD', 4127: 'SWKS', 4281: 'HWM', 4447: 'HES', 4904: 'AEP', 4962: 'AXP', 4977: 'AFL', 5272: 'AIG', 5513: 'UNM', 6201: 'AAL', 6281: 'ADI', 6769: 'APA', 6951: 'AMAT', 7084: 'ADM', 8670: 'ADP', 8818: 'AVY', 9389: 'BLL', 10456: 'BAX', 10795: 'BDX', 11544: 'WRB', 12208: 'BIO', 12927: 'BA', 14272: 'BMY', 14693: 'BF.B', 16732: 'CPB', 16918: 'STZ', 18230: 'CAT', 18926: 'LUMN', 19617: 'JPM', 20286: 'CINF', 21076: 'CLX', 21344: 'KO', 21665: 'CL', 23217: 'CAG', 24545: 'TAP', 24741: 'GLW', 26172: 'CMI', 27419: 'TGT', 27904: 'DAL', 28412: 'CMA', 29534: 'DG', 29905: 'DOV', 29989: 'OMC', 30625: 'FLS', 31462: 'ECL', 31791: 'PKI', 32604: 'EMR', 33185: 'EFX', 34088: 'XOM', 34903: 'FRT', 35527: 'FITB', 36104: 'USB', 36270: 'MTB', 37785: 'FMC', 37996: 'F', 38777: 'BEN', 39911: 'GPS', 40533: 'GD', 40545: 'GE', 40704: 'GIS', 40987: 'GPC', 45012: 'HAL', 46080: 'HAS', 47111: 'HSY', 47217: 'HPQ', 48039: 'HFC', 48465: 'HRL', 49071: 'HUM', 49196: 'HBAN', 49826: 'ITW', 50863: 'INTC', 51143: 'IBM', 51253: 
'IFF', 51434: 'IP', 51644: 'IPG', 52988: 'J', 54480: 'KSU', 55067: 'K', 55785: 'KMB', 56873: 'KR', 58492: 'LEG', 59478: 'LLY', 59558: 'LNC', 60086: 'L', 60667: 'LOW', 62709: 'MMC', 62996: 'MAS', 63754: 'MKC', 63908: 'MCD', 64040: 'SPGI', 64803: 'CVS', 65984: 'ETR', 66740: 'MMM', 68505: 'MSI', 70858: 'BAC', 72741: 'ES', 72903: 'XEL', 72971: 'WFC', 73124: 'NTRS', 73309: 'NUE', 74208: 'UDR', 75362: 'PCAR', 75677: 'PKG', 76334: 'PH', 77360: 'PNR', 77476: 'PEP', 78003: 'PFE', 78239: 'PVH', 79879: 'PPG', 80424: 'PG', 80661: 'PGR', 84839: 'ROL', 86312: 'TRV', 87347: 'SLB', 89800: 'SHW', 91142: 'AOS', 91419: 'SJM', 
91440: 'SNA', 91576: 'KEY', 92122: 'SO', 92230: 'TFC', 92380: 'LUV', 93410: 'CVX', 93556: 'SWK', 93751: 'STT', 96021: 'SYY', 96943: 'TFX', 97210: 'TER', 97476: 'TXN', 97745: 'TMO', 100493: 'TSN', 100517: 'UAL', 100885: 'UNP', 101778: 'MRO', 101829: 'RTX', 103379: 'VFC', 104169: 'WMT', 105770: 'WST', 106040: 'WDC', 106535: 'WY', 106640: 'WHR', 107263: 'WMB', 109198: 'TJX', 109380: 'ZION', 200406: 'JNJ', 202058: 'LHX', 203527: 'VAR', 217346: 'TXT', 277135: 'GWW', 277948: 'CSX', 310158: 'MRK', 310764: 'SYK', 313616: 'DHR', 313927: 'CHD', 315189: 'DE', 315213: 'RHI', 315293: 'AON', 316709: 'SCHW', 318154: 'AMGN', 319201: 'KLAC', 320187: 'NKE', 320193: 'AAPL', 320335: 'GL', 352541: 'LNT', 352915: 'UHS', 354190: 'AJG', 354908: 'FLIR', 354950: 'HD', 701985: 'LB', 702165: 'NSC', 707549: 'LRCX', 711404: 'COO', 712515: 'EA', 713676: 'PNC', 715957: 'D', 718877: 'ATVI', 719739: 'SIVB', 720005: 'RJF', 721371: 'CAH', 723125: 'MU', 723254: 'CTAS', 723531: 'PAYX', 726728: 'O', 728535: 'JBHT', 731766: 'UNH', 731802: 'ATO', 732712: 'VZ', 732717: 'T', 740260: 'VTR', 743316: 'MXIM', 743988: 'XLNX', 745732: 'ROST', 746515: 'EXPD', 749251: 'IT', 753308: 'NEE', 759944: 'CFG', 764180: 'MO', 764478: 'BBY', 764622: 'PNW', 765880: 'PEAK', 766421: 'ALK', 766704: 'WELL', 769397: 'ADSK', 773840: 'HON', 779152: 'JKHY', 783280: 'DRE', 783325: 'WEC', 788784: 'PEG', 789019: 'MSFT', 789570: 'MGM', 796343: 'ADBE', 797468: 'OXY', 798354: 'FISV', 804328: 'QCOM', 804753: 'CERN', 811156: 'CMS', 813672: 'CDNS', 813828: 'VIAC', 814453: 'NWL', 815094: 'ABMD', 815097: 'CCL', 815556: 'FAST', 818479: 'XRAY', 820027: 'AMP', 820313: 'APH', 821189: 'EOG', 822416: 'PHM', 823768: 'WM', 827052: 'EIX', 827054: 'MCHP', 829224: 'SBUX', 831001: 'C', 831259: 'FCX', 832101: 'IEX', 833444: 'JCI', 849399: 'NLOK', 851968: 'MHK', 858470: 'COG', 858877: 'CSCO', 859737: 'HOLX', 860730: 'HCA', 860731: 'TYL', 864749: 'TRMB', 865752: 'MNST', 866787: 'AZO', 872589: 'REGN', 874716: 'IDXX', 874761: 'AES', 874766: 'HIG', 875045: 'BIIB', 875320: 'VRTX', 877212: 'ZBRA', 877890: 'CTXS', 
878927: 'ODFL', 879101: 'KIM', 879169: 'INCY', 882095: 'GILD', 882184: 'DHI', 882835: 'ROP', 883241: 'SNPS', 884887: 'RCL', 885725: 'BSX', 886982: 'GS', 895421: 'MS', 896159: 'CB', 896878: 'INTU', 898173: 
'ORLY', 899051: 'ALL', 899689: 'VNO', 899866: 'ALXN', 900075: 'CPRT', 906107: 'EQR', 906163: 'NVR', 908255: 'BWA', 909832: 'COST', 910606: 'REG', 912595: 'MAA', 914208: 'IVZ', 915389: 'EMN', 915912: 'AVB', 915913: 'ALB', 916076: 'MLM', 916365: 'TSCO', 920148: 'LH', 920522: 'ESS', 920760: 'LEN', 922224: 'PPL', 927066: 'DVA', 927628: 'COF', 927653: 'MCK', 935703: 'DLTR', 936340: 'DTE', 936468: 'LMT', 940944: 
'DRI', 943452: 'WAB', 943819: 'RMD', 945841: 'POOL', 946581: 'TTWO', 1000228: 'HSIC', 1000697: 'WAT', 1001082: 'DISH', 1001250: 'EL', 1002047: 'NTAP', 1002910: 'AEE', 1012100: 'SEE', 1013462: 'ANSS', 1013871: 'NRG', 1014473: 'VRSN', 1018724: 'AMZN', 1020569: 'IRM', 1021860: 'NOV', 1022079: 'DGX', 1024478: 'ROK', 1031296: 'FE', 1032208: 'SRE', 1034054: 'SBAC', 1035002: 'VLO', 1035267: 'ISRG', 1035443: 'ARE', 1037038: 'RL', 1037540: 'BXP', 1037646: 'MTD', 1037868: 'AME', 1038357: 'PXD', 1039684: 'OKE', 1040971: 'SLG', 1041061: 'YUM', 1043277: 'CHRW', 1043604: 'JNPR', 1045609: 'PLD', 1045810: 'NVDA', 1047862: 'ED', 1048286: 'MAR', 1048695: 'FFIV', 1048911: 'FDX', 1050915: 'PWR', 1051470: 'CCI', 1053507: 'AMT', 1058090: 'CMG', 1058290: 'CTSH', 1059556: 'MCO', 1060391: 'RSG', 1063761: 'SPG', 1065088: 'EBAY', 1065280: 'NFLX', 1065696: 'LKQ', 1067701: 'URI', 1067983: 'BRK.B', 1070750: 'HST', 1071739: 'CNC', 1075531: 'BKNG', 1086222: 'AKAM', 1090012: 'DVN', 1090727: 'UPS', 1090872: 'A', 1091667: 'CHTR', 1093557: 'DXCM', 1094285: 'TDY', 1095073: 'RE', 1097149: 'ALGN', 1099219: 'MET', 1099800: 'EW', 1101239: 'EQIX', 1103982: 'MDLZ', 1108524: 'CRM', 1109357: 'EXC', 1110803: 'ILMN', 1111711: 'NI', 1111928: 'IPGP', 1113169: 'TROW', 1116132: 'TPR', 1120193: 'NDAQ', 1121788: 'GRMN', 1123360: 'GPN', 1126328: 'PFG', 1130310: 'CNP', 1132979: 'FRC', 1133421: 'NOC', 1136869: 'ZBH', 1136893: 'FIS', 1137774: 'PRU', 1137789: 'STX', 1138118: 'CBRE', 1140536: 'WLTW', 1140859: 'ABC', 1141391: 'MA', 1156039: 'ANTM', 1156375: 'CME', 1158449: 'AAP', 1163165: 'COP', 1164727: 'NEM', 1166691: 'CMCSA', 1170010: 'KMX', 1174922: 'WYNN', 1175454: 'FLT', 1260221: 'TDG', 1262039: 'FTNT', 1267238: 'AIZ', 1278021: 'MKTX', 1281761: 'RF', 1283699: 'TMUS', 1285785: 'MOS', 1286681: 'DPZ', 1289490: 'EXR', 1297996: 'DLR', 1300514: 'LVS', 1306830: 'CE', 1318605: 'TSLA', 1324404: 'CF', 1324424: 'EXPE', 1326160: 'DUK', 1326801: 'FB', 1335258: 'LYV', 1336917: 'UAA', 1336920: 'LDOS', 1341439: 'ORCL', 1359841: 'HBI', 1364742: 'BLK', 1365135: 'WU', 1370637: 'ETSY', 1373715: 'NOW', 1374310: 'CBOE', 1378946: 'PBCT', 1383312: 'BR', 1385157: 'TEL', 1390777: 'BK', 1393311: 'PSA', 1393612: 'DFS', 1396009: 'VMC', 1402057: 'CDW', 1403161: 'V', 1403568: 'ULTA', 1408198: 'MSCI', 1410636: 'AWK', 1413329: 'PM', 1418091: 'TWTR', 1437107: 'DISCA', 1442145: 'VRSK', 1463101: 'ENPH', 1466258: 'TT', 1467373: 'ACN', 1467858: 'GM', 1478242: 'IQV', 1489393: 'LYB', 1492633: 'NLSN', 1501585: 'HII', 1506307: 'KMI', 1510295: 'MPC', 1513761: 'NCLH', 1519751: 'FBHS', 1521332: 'APTV', 1524472: 'XYL', 1534701: 'PSX', 1539838: 'FANG', 1551152: 'ABBV', 1551182: 'ETN', 1555280: 'ZTS', 1564708: 'NWSA', 1571949: 'ICE', 1579241: 'ALLE', 1585364: 'PRGO', 1585689: 'HLT', 1590955: 'PAYC', 1596532: 'ANET', 1596783: 'CTLT', 1598014: 'INFO', 1601046: 'KEYS', 1601712: 'SYF', 1604778: 'QRVO', 1613103: 'MDT', 1618921: 'WBA', 1633917: 'PYPL', 1637459: 'KHC', 1645590: 'HPE', 1652044: 'GOOGL', 1659166: 'FTV', 1666700: 'DD', 1679273: 'LW', 1681459: 'FTI', 1688568: 'DXC', 1699150: 'IR', 1701605: 'BKR', 1707925: 'LIN', 1711269: 'EVRG', 1730168: 'AVGO', 1732845: 'WRK', 1739940: 'CI', 1744489: 'DIS', 1748790: 'AMCR', 1751788: 'DOW', 1754301: 'FOXA', 1755672: 'CTVA', 1757898: 'STE', 1770450: 'XRX', 1773383: 'DT', 1781335: 'OTIS', 1783180: 'CARR', 1786842: 'VNT', 1792044: 'VTRS'}

def build_cik_ticker():
    companies_ciks = comp_col.distinct("cik")
    # Add ciks from manually defined ciks list
    for cik in ciks:
        if cik not in companies_ciks:
            companies_ciks.append(cik)
    for cik in companies_ciks:
        if cik not in ciks:
            ciks.append(cik)
        comp_data = comp_col.find_one({"cik": cik})
        ticker = comp_data['ticker']
        if isinstance(ticker, str):
            cik_ticker[cik] = ticker
        else:
            cik_ticker[cik] = "n/a"
    # print(cik_ticker)
    print(ciks)

def build_cik_ticker_sec():
    # ticker_data = sec_ticker_col.find()
    # print(ticker_data)
    df = pd.DataFrame(list(sec_ticker_col.find()))
    print(df.head())
    df['ticker'] = df['ticker'].str.upper()
    global cik_ticker
    global ticker_cik
    cik_ticker = dict(zip(df['cik'], df['ticker']))
    ticker_cik = dict(zip(df['ticker'], df['cik']))
    # print(cik_ticker)

def build_ticker_cik():
    """ Builds tickers and ticker_cik variables from database """
    companies_tickers = comp_col.distinct("ticker")
    for ticker in companies_tickers:
        if ticker not in tickers:
            tickers.append(ticker)
        comp_data = comp_col.find_one({"ticker": ticker})
        cik = comp_data['cik']
        if ticker not in ticker_cik:
            ticker_cik[ticker] = cik
    # print(tickers)
    # print(ticker_cik)

### Queries MongoDB and adds results to Dataframe ###
### query = MongoDB query
### dataset = MongoDB dataset to query
### df = Dataframe to add the results to
### value_column = Dataframe column to add the value to
### tag_column = Dataframe column to add the tag to
### returns modified dataframe
def find_and_add_to_df(query, dataset, df, value_column, tag_column):
    query_result = dataset.find(query)
    for result in query_result:
        df.loc[result['ddate']].at[value_column] = result['value']
        df.loc[result['ddate']].at[tag_column] = result['tag']
    return df


def find_and_add_to_df_if_nan(query, dataset, df, value_column, tag_column):
    df_copy = df.copy()
    df_copy.reset_index(inplace=True)
    # df_copy.rename(columns={"index": "statement_date"}, inplace=True)
    # print(df_copy)
    query_result = dataset.find(query)
    for result in query_result:
        # print(str(result['ddate']) + "  " + result['tag'] + "  " + str(result['value']))
        if pd.isna(df.loc[result['ddate']].at[value_column]):
            # print("Found null ddate: " + str(result['ddate']))
            index_num = df_copy[df_copy['index'] == result['ddate']].index.values.astype(int)[0]
            qtr_count = 0
            history = []
            if index_num > 3:
                while qtr_count < 4 and index_num > 3:
                    index_num = index_num - 1
                    # print("index_num: " + str(index_num) + "  value: " + str(df.iloc[index_num][value_column]))
                    if not pd.isna(df.iloc[index_num][value_column]):
                        try:
                            history.append(float(df.iloc[index_num][value_column]))
                        except:
                            history.append(0)
                            print("Issue appending to history: " + str(df.iloc[index_num][value_column]))
                        # print("APPENDED - index_num: " + str(index_num) + "  value: " + str(df.iloc[index_num][value_column]))
                        qtr_count = qtr_count + 1
                three_prev_qtrs_sum = sum(history)
                # print("Three quarter sum: " + str(three_prev_qtrs_sum))
                qtr_val = result['value'] - three_prev_qtrs_sum
                df.loc[result['ddate']].at[value_column] = qtr_val
                df.loc[result['ddate']].at[tag_column] = result['tag']
    return df

### Not used - Possible use in modularizing code more ###
def insert_company_record(cik, company):
    calc_col.insert_one({"cik": cik, "company": company})

### Not used - Possible use in modularizing code more ###
def upsert_array_object(cik, company, array, object_name, value):
    calc_col.update_one({"cik": cik, "company": company}, {"$push": {array: {object_name: value}}}, upsert=True)
