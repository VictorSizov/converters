import os
import shutil
import time

cmddir = '.\\comm'
templdir = 'templates'
cmdext = '.cmd'
templext = '.templ'
templprefix='validator_'
nppexecini = 'NppExec.ini'
nppexeccmd = 'npes_saved.txt'
paths_names = ['CORPUS_PATH', 'INPUT_PATH',  'SCHEMA_PATH', 'IGNORE_PATH']


def ask():
    if os.path.exists(cmddir):
        while True:
            ret = input('validator is installed yet. Reinstall (Y/N)?').lower()[0]
            if ret == 'n':
                print('installation stopped')
                return ''
            if ret == 'y':
                break
        shutil.rmtree(cmddir)
        time.sleep(.1)
    os.mkdir(cmddir,)
    use_basepath = input('Has corpus components common basic path or not (Y/N)?').lower()[0]
    if use_basepath == 'n':
        return '?'
    while True:
        basepath = input('input ruscorpora basic path (like c:/place/ruscorpora/corpora) or empty string for exit:')
        if basepath == '' or  os.path.exists(basepath):
            break
        print("Path {0} isn't exists".format(basepath))
    return basepath


def err_report(fname, line, mess):
    return 'File "{0}, line {1}\n{2}\n'.format(fname, line, mess)


def expand_var(var):
    while True:
        value = os.path.expandvars(var)
        if value == var:
            break
        var = value
    return value


def check_templ(templ_name, tmpl_data):
    paths_names_cpy = list(paths_names)
    err = ''
    count = 0
    # os.environ['BASE'] = basepath
    for line in tmpl_data.split('\n'):
        count += 1
        if line[:4] != 'set ':
            continue
        pair = line[4:].strip().split('=')
        if len(pair) != 2:
            err += 'error: syntax error (template: {0}, line {1}\n'.format(templ_name, count)
        name, value = pair[0].strip(), pair[1].strip()
        if name in paths_names_cpy:
            paths_names_cpy.remove(name)
            check_path = expand_var(value)
            if not os.path.exists(check_path):
                if name == 'CORPUS_PATH':
                    return ''
                err += 'error: path {0} not exists (template: {1}, name: {2}\n'.format(check_path, templ_name, name)
        os.environ[name] = value
    if paths_names_cpy and paths_names_cpy != ['SCHEMA_PATH']:
        err += 'error: name(s) {0} are not defined (template: {1})\n'.format(','.join(paths_names_cpy), templ_name)
    if err:
        return err


def templ_process(basepath, currpath, templ_name):
    comm_name = templ_name.replace(templext, cmdext)
    if os.path.exists(comm_name):
        return ''
    with open(os.path.join(templdir, templ_name), encoding="utf-8") as tmpl:
        tmpl_data = tmpl.read()
    if basepath != '?':
        headstr = 'echo off\nset SCRIPT_PATH={0}\nset BASE={1}\n'.format(currpath, basepath)
    else:
        corpname=templ_name.replace(templprefix,"").replace(templext,"")
        while True:
            corpus_path = input("Input path to corpus {0} or empty string to skip it:".format(corpname))
            if corpus_path == '':
                return ''
            if os.path.exists(corpus_path):
                break
            print("Path {0} isn't exists".format(corpus_path))
        headstr = 'echo off\nset SCRIPT_PATH={0}\nset CORPUS_PATH={1}\n'.format(currpath, corpus_path)
        tmpl_data = tmpl_data.replace("set CORPUS_PATH=","rem set CORPUS_PATH=")
    tmpl_data = headstr + tmpl_data
    err = check_templ(templ_name, tmpl_data)
    if err is not None:
        return err
    comm_name2 = os.path.join(cmddir, comm_name)
    with open(comm_name2, 'w', encoding="utf-8") as comm:
        comm.write(tmpl_data)
    cmdname = comm_name[10:-1 * len(cmdext)]
    cmdvalue = os.path.join(currpath, comm_name2)
    ret = '::{0}\n{1}\n'.format(cmdname, cmdvalue)
    return ret


def init():
    curYd=os.getcwd()
    basepath = ask()
    if basepath == '':
        return
    currpath = os.path.dirname(os.path.abspath(__file__))
    npppath = os.path.join(os.environ['appdata'], 'Notepad++/plugins/config')

    shutil.copyfile(os.path.join(templdir, nppexecini), os.path.join(npppath, nppexecini))
    nppexeccmd1 = os.path.join(npppath, nppexeccmd)
    nppexeccmd2 = nppexeccmd1 + '.bak'
    if os.path.exists(nppexeccmd1):
        if os.path.exists(nppexeccmd2):
            os.remove(nppexeccmd2)
        os.rename(nppexeccmd1, nppexeccmd2)
    files = [f for f in os.listdir(templdir) if f[-6:] == templext]
    with open(nppexeccmd1, "w", encoding="utf-8") as nppe:
        for f in files:
            f_descr = templ_process(basepath, currpath, f)
            if f_descr == '':
                continue
            if f_descr[:6] == 'error ':
                print(os.path.join(templdir, f), f_descr)
                continue
            nppe.write(f_descr)
    print("Installation has done.")


if __name__ == '__main__':
    init()
