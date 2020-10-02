try:
    from chaizi_reverse import HanziChaizi
except:
    from mdict.mdict_utils.chaizi_reverse import HanziChaizi

hc=HanziChaizi()

# hc.convert_original()
# print(hc.query('嶌'))
# hc.convert_reverse()
print(hc.reverse_query('山鳥'))
#key={'嶌':[['山','鳥']]}
# hc.add_new_chaizi(key)