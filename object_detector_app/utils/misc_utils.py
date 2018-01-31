import subprocess

def is_using_tensorflow_gpu():
    '''
        HACK:: Anshuman 01/31/2017

        Can't seem to figure out a way if we are using tensorflow-gpu
        or tensorflow from just the module. So going to use pip freeze
        to figure out if the env (or virtualenv) has tensorflow-gpu
        isntalled.
    '''
    cmd = "pip freeze | grep 'tensorflow-gpu' | wc -l"
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    stdout, stderr = p.communicate()

    # if there is an error for some reason just return False
    if stderr:
        return False

    return stdout.split()[0] == 1
