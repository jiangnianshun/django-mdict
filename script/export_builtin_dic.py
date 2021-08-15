import os
import sys
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
import django

django.setup()

from base.base_func import ROOT_DIR
from mdict.mdict_utils.search_utils import get_mdict_content
from mdict.models import MyMdictEntry

builtin_dic_prefix = '''
<link rel='stylesheet' href='/static/bootstrap/css/bootstrap.min.css'>
<link rel='stylesheet' href='/static/mdict/css/mdict.css'>
<script>
    function elementDisplay(objname){
        var obj=document.getElementsByName(objname);
        for(var i=0;i<obj.length;i++){
            if(obj[i].style.display !='none'){
                obj[i].style.display='none';
            }else{
                obj[i].style.display='block';
            }
        }
    }
</script>
'''

static_list = [r'static\bootstrap\css\bootstrap.min.css', r'mdict\static\mdict\css\mdict.css']
# r'mdict\static\mdict\MathJax-master'

export_root_path = os.path.join(ROOT_DIR, 'export')
export_txt_path = os.path.join(ROOT_DIR, 'export', 'export.txt')

export_data_root_path = os.path.join(export_root_path, 'data')

uploads_path = os.path.join(ROOT_DIR, 'media', 'uploads')
export_uploads_path = os.path.join(export_data_root_path, 'media', 'uploads')


def export_to_txt():
    entry_list = MyMdictEntry.objects.all()
    i = 1
    mdict_list = []
    for entry in entry_list:
        mdict_entry = entry.mdict_entry
        mdict_content = ''.join(get_mdict_content(entry)).replace('\r', '').replace('\n', '')
        mdict = mdict_entry + builtin_dic_prefix + mdict_content + '\n</>'
        # mdict_static_file前后自动带\n

        i += 1
        mdict_list.append(mdict)
    if not os.path.exists(export_root_path):
        os.mkdir(export_root_path)
    if os.path.exists(export_data_root_path):
        shutil.rmtree(export_data_root_path)
    os.mkdir(export_data_root_path)
    if os.path.exists(export_uploads_path):
        shutil.rmtree(export_uploads_path)

    with open(export_txt_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(mdict_list))
    os.chmod(export_txt_path, 0o777)

    for s in static_list:
        data_path = os.path.join(ROOT_DIR, s)
        if os.path.isfile(data_path):
            s_name = os.path.basename(data_path)
            target_path = os.path.join(export_data_root_path, s_name)
            print(target_path)
            shutil.copy(data_path, target_path)
        else:
            a = s[s.find('static'):]
            target_path = os.path.join(export_data_root_path, a)
            print(target_path)
            shutil.copytree(data_path, target_path)
    print(uploads_path)
    shutil.copytree(uploads_path, export_uploads_path)

    print('已导出到mynav/export，导出完成。')


export_to_txt()
