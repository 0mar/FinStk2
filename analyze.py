import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_curve, confusion_matrix, roc_auc_score, precision_score
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import PolynomialFeatures

def make_Xy(df, consider, predict, timeDelta = 5, futureTime = 1, timeHistory = 365):

    #aheadTime #of days before we make prediction
    #timeDelta #of previous days to consider when making prediction

    df.reset_index(inplace = True)

    # Dual column indices:
    # Make new indexing as the df is going to be formatted heavily.
    # Rows timeDelta days will be transformed into columns with data and day labels.
    comps = np.reshape(np.array([np.repeat(comp[0].strip(), timeDelta) for comp in consider]), len(consider)*timeDelta)
    arr = np.reshape(np.array([['{:s}_{:d}'.format(val[1],-(i+1)) for i in range(timeDelta)] for val in consider]), timeDelta*len(consider))

    col_tuples = list(zip(*[comps, arr]))
    index = pd.MultiIndex.from_tuples(col_tuples, names=['company', 'values'])
    df_X = pd.DataFrame(columns = index)
    #df_y = pd.Series(name = predict[0])
    df_y = pd.DataFrame(columns = range(futureTime))

    for i in range(futureTime, timeHistory):
        # pick data from days that are BEFORE the now considered day i. The dates are arranged
        # descendind order.
        df_l = df.iloc[i + 1 : i + 1 + timeDelta][consider]
        # Reshape the matrix into one long vector
        data = np.reshape(df_l.values, timeDelta*len(consider), order = 'F')
        df_X.loc[i] = data
        #df_y.loc[i] = df.iloc[i][predict].values.tolist()[0]

        # For the prediction pick values TODAY and some days (futureTime) ahead.
        df_y.loc[i] =[1 + .01*df.iloc[i - add][predict].values[0] for add in range(futureTime)]
        #print(data, (df_y.loc[i].values - 1)*100)
    #df_X.drop(predict[0][0], axis = 1, inplace = True)
    return df_X, df_y


def get_Xy(init_features, predict, pick_comps = [], timeDelta = 5, futureTime = 3, timeHistory = 365):

    df = pd.read_pickle('combined.pkl')
    l1, l2 = zip(*df.columns.values)
    companies = list(set(l1))
    values = list(set(l2))

    l1, l2 = zip(*df.columns.values.tolist())

    # Predict with these:
    # values_pick = ['Oe_price_change_%', 'Change M. Eur'] #'L_price_change_%' 'Change M. Eur'

    excl_comp_list = ['Ahola Transport A', 'Aktia Pankki R', 'Asiakastieto Group', 'Consti Yhtiöt',
                      'DNA', 'Detection Technology', 'Digitalist Group', 'Dovre Group',
                      'Elite Varainhoito', 'Evli Pankki', 'Elecster A','Ericsson B',
                      'FIT Biotech', 'Fondia', 'Heeros', 'Ilkka-Yhtymä I', 'Ilkka-Yhtymä II',
                      'Kamux Oyj', 'Kotipizza Group', 'Kesla A',
                      'Lehto Group', 'Nexstim', 'Next Games', 'Nixu', 'Nurminen Logistics', 'Pihlajalinna',
                      'Piippo', 'Pohjois-Karjalan Kirjapaino', 'PKC Group', 'Privanet Group',
                      'Qt Group', 'Remedy Entertainment',
                      'Robit', 'Savo-Solar', 'Silmäasema Oyj', 'Soprano', 'Sievi Capital',
                      'Suomen Hoivatilat', "Trainers' House", 'Tulikivi A','Tecnotree',
                      'Talenom', 'Talvivaara', 'Tokmanni Group', 'United Bankers',
                      'Vincit Group', 'Yleiselektroniikka E', 'Wulff-Yhtiöt', 'Zeeland Family',
                      'Ålandsbanken A']

    if len(pick_comps) != 0:
        rem_comps2 = [comp for comp in companies if comp not in pick_comps]
        excl_comp_list += rem_comps2

    for comp in list(set(excl_comp_list)):
        companies.remove(comp)



    companies_pick = np.repeat(np.array(sorted(companies)), len(init_features))
    #predict = [(comp_predict, val_predict)]

    consider = list(zip(*[companies_pick, init_features*len(companies)]))
    dfX, dfy = make_Xy(df, consider, predict, timeDelta, futureTime, timeHistory)

    return dfX, dfy, df

def plot_stock(df, comp, features  = ['Offer Sell']):

    #x = y.index.values.tolist()
    x = -df.index.values
    plt.figure(figsize = (20, 7))
    [y0, y1] = [df[(comp, features[i])].values.tolist() for i in range(2)]

    plt.plot(x,y0, label = features[0])
    for xc in x:
        plt.axvline(x=xc, alpha = .2)
    plt.legend(loc = 2, frameon = False)


    ax2 = plt.gca().twinx()
    ax2.plot(x,y1, c = 'red', label = features[1])

    plt.xlabel('days')
    plt.title(comp)
    plt.legend(loc = 1, frameon = False)
    plt.show()

def fit_Learner(comp, pick_comps, threshold = .5, plot_stock = False):

    #comp = 'Affecto'

    nfut = 2
    ndays = 10
    nhist = 365*2

    # 'L_price_change', 'L_price_change_%', 'H_price_change',
    # 'Oe_price_change', 'Offer Sell', 'H_price_change_%',
    # 'Change M. Eur', 'Sales Highest', 'Oe_price_change_%',
    # 'Offer Buy', 'Offer End', 'Sales Lowest'
    init_features = ['Oe_price_change_%', 'L_price_change_%', 'H_price_change_%', 'Change M. Eur'] #'L_price_change_%' 'Change M. Eur'
    predict = [(comp, 'L_price_change_%')]


    X, y, df = get_Xy(init_features, predict, pick_comps, ndays, nfut, nhist)
    col_names = X[comp].columns.values.tolist()
    #y['1x2'] = y[0].multiply(y[1], axis="index")
    y = (y.prod(axis = 1) - 1)*100
    #y = y.max(axis = 1)

    #

    bad = []
    for col in X.columns.values.tolist():
        if 10 < sum(X[col].isnull()):
            if col[0] not in bad: bad.append(col[0])

    if 5 < sum(y.isnull()):
        print('YYYYYYYYYYYYYYYYYYYYY')

    X.fillna(method='bfill', inplace = True)
    y.fillna(method='bfill', inplace = True)
    X.fillna(method='ffill', inplace = True)
    y.fillna(method='ffill', inplace = True)

    if plot_stock: plot_stock(df, comp, ['Sales Lowest', 'L_price_change_%'])

    poly = PolynomialFeatures(degree=2, interaction_only=True)
    X = poly.fit_transform(X)
    #print(X)

    y =  y > threshold
    X_train = X[int(nhist*.25):]
    y_train = y[int(nhist*.25):]
    X_test = X[:int(nhist*.25)]
    y_test = y[:int(nhist*.25)]

    #l1, l2 = zip(*X_train.columns.values.tolist())
    #print(list(l1))
    '''
    {'max_features': 5, 'max_depth': 7, 'n_estimators': 600}
    {'max_features': 10, 'max_depth': 10, 'n_estimators': 800}
    {'n_estimators': 1000, 'max_features': 7, 'max_depth': 12}
    {'n_estimators': 1000, 'max_features': 7, 'max_depth': 12}

    '''
    rf = RandomForestClassifier(n_estimators = 750, max_depth = 12, max_features = 7)
    # 'n_estimators': 750, 'max_depth': 15, 'max_features': 5
    param_grid = {'max_features': [5, 7, 10],
                  'max_depth': [12, 15],
                  'n_estimators': [800, 1000]}

    #grid_rf = GridSearchCV(rf, param_grid, scoring='roc_auc', verbose = 3, cv = 4)
    grid_rf = rf
    grid_rf.fit(X_train, y_train)

    y_pred = grid_rf.predict(X_test)
    y_pred_p = grid_rf.predict_proba(X_test)[:,1]

    y_pred_p_train = grid_rf.predict_proba(X_train)[:,1]


    fpr, tpr, _ = roc_curve(y_test, y_pred_p)
    roc_auc_s = roc_auc_score(y_test, y_pred_p)
    precision_s = precision_score(y_test, y_pred)

    roc_auc_s_train = roc_auc_score(y_train, y_pred_p_train)

    print('{:s}: precision = {:.2f}, roc_auc_score = {:.2f}, roc_auc_score_train = {:.2f}'.format(comp,
     precision_s, roc_auc_s, roc_auc_s_train))
    print(classification_report(y_test, y_pred))
    print(confusion_matrix(y_test, y_pred))
    print()


    # Try to imporive by removing features
    feat_importance = grid_rf.feature_importances_
    fraction = .10
    ordered_features = np.argsort(feat_importance)[::-1]
    #print()
    feat_names = poly.get_feature_names(col_names)
    for i in ordered_features[:50]:
        print(feat_names[i])
    f, [ax1, ax2] = plt.subplots(2, figsize = (12,12))
    ax1.plot(fpr, tpr)
    ax1.plot([0,1], [0,1])
    ax2.bar(range(len(ordered_features)),
            feat_importance[ordered_features], 1, color="blue", alpha = .8)
    ax2.axvline(x=int(len(ordered_features)/10), alpha = .5)
    plt.show()

    for frac in np.arange(.01, .2, .01):
        print('fraction = {:.2f}'.format(frac))
        pick_features = ordered_features[:int(len(feat_importance)*frac)]
        X_e = X[:, pick_features]
        X_e_train = X[int(nhist*.25):]
        X_e_test = X[:int(nhist*.25)]

        grid_rf.fit(X_e_train, y_train)
        y_pred = grid_rf.predict(X_e_test)
        y_pred_p = grid_rf.predict_proba(X_e_test)[:,1]

        y_pred_p_train = grid_rf.predict_proba(X_e_train)[:,1]
        roc_auc_s = roc_auc_score(y_test, y_pred_p)
        precision_s = precision_score(y_test, y_pred)

        roc_auc_s_train = roc_auc_score(y_train, y_pred_p_train)

        print('{:s}: precision = {:.2f}, roc_auc_score = {:.2f}, roc_auc_score_train = {:.2f}'.format(comp,
        precision_s, roc_auc_s, roc_auc_s_train))
        print(classification_report(y_test, y_pred))
        print(confusion_matrix(y_test, y_pred))
        print()

    #for xc in [i*ndays*len(init_features) for i in range(ndays)]:
    #    ax2.axvline(x=xc, alpha = .2)
    #ax2.axvline(x=, alpha = .5)
    #print(grid_rf.best_params_) #{'max_features': 200, 'n_estimators': 1000, 'max_depth': 30}
    #print(grid_rf.best_score_)
    #print(grid_rf.best_estimator_.feature_importances_)


    #plt.show()
    return roc_auc_s

comps = ['Afarak Group', 'Affecto', 'Ahlstrom-Munksjö', 'Aktia Pankki A',
      'Alma Media', 'Amer Sports A', 'Apetit', 'Aspo',
      'Aspocomp Group', 'Atria A', 'Basware', 'Biohit B', 'Bittium',
      'CapMan', 'Cargotec', 'Caverion', 'Citycon', 'Cleantech Invest',
      'Componenta', 'Cramo', 'Digia',
      'Efore', 'Elisa', 'Endomines',
      'Etteplan', 'Exel Composites', 'F-Secure', 'Finnair',
      'Fiskars', 'Fortum', 'Glaston', 'HKScan A', 'Herantis Pharma',
      'Honkarakenne B', 'Huhtamäki',
      'Incap', 'Innofactor', 'Investors House', 'Kemira', 'Keskisuomalainen A',
      'Kesko A', 'Kesko B', 'Kone', 'Konecranes', 'Lassila & Tikanoja',
      'Lemminkäinen', 'Marimekko', 'Martela A', 'Metso', 'Metsä Board A',
      'Metsä Board B', 'Neo Industrial', 'Neste', 'Nokia', 'Nokian Renkaat',
      'Nordea Bank',  'OMXH25 ETF', 'Olvi A',
      'Orava Asuntorahasto', 'Oriola A', 'Oriola B', 'Orion A',
      'Orion B', 'Outokumpu', 'Outotec', 'Panostaja',
      'Ponsse', 'Pöyry', 'QPR Software',
      'Raisio K', 'Raisio V', 'Ramirent', 'Rapala VMC', 'Raute A',
      'Restamax', 'Revenio Group', 'SRV Yhtiöt', 'SSAB A', 'SSAB B',
      'SSH Comm. Security', 'Saga Furs C', 'Sampo A', 'Sanoma',
      'Scanfil', 'Siili Solutions', 'Solteq',
      'Sotkamo Silver', 'Sponda', 'Stockmann A', 'Stockmann B',
      'Stora Enso A', 'Stora Enso R', 'Suominen', 'Taaleri', 'Technopolis',
      'Teleste', 'Telia Company', 'Tieto', 'Tikkurila',
      'UPM-Kymmene', 'Uponor',
      'Uutechnic Group', 'Vaisala A', 'Valmet', 'Valoe', 'Verkkokauppa.com',
      'Viking Line', 'Wärtsilä', 'YIT',
      'eQ', 'Ålandsbanken B'] #


sum_ra = 0
threshold = 2 #%

for comp in comps:
    sum_ra += fit_Learner(comp, [comp], threshold)




print('roc_auc average')
print(sum_ra/len(comps))
