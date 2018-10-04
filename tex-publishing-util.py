import sys
import os
import glob
import re
import argparse
import shutil 
import tempfile
from PIL import Image
import random
import string
import glob2
from huepy import *

# What extensions should be converted to jpg
EXT = ['png', 'tiff']

def main():
    parser = argparse.ArgumentParser(description='Minify your `LaTeX` project for publication.')
    parser.add = parser.add_argument

    parser.add('--project-dir', required=True, type=str, help='Path to LaTeX project directory.')
    parser.add('--main-file',   required=True, type=str, default='main.tex', help='Name of the file that you compile.')

    parser.add('--save-dir',    required=True, type=str, default="", help='Where to save the processed project.')

    parser.add('--remove-redundant-files', action='store_true', help='Clean up redundant files')
    parser.add('--remove-comments',        action='store_true', help='Remove comments within the .tex files.')

    parser.add('--flatten',                action='store_true', help='Converts the project to a one without any folders (flat structure).')

    parser.add('--convert-to-jpg',         action='store_true', help='Convert image files to jpg.')
    parser.add('--quality',                type=int, default=98,help='Conversion quality.')

    parser.add('--debug',                  action='store_true', help='Do not suppress the intermediate output.')

    args = parser.parse_args()


    # Remove what's there in `save_dir`
    save_dir    = args.save_dir
    if os.path.exists(save_dir):
        print(red(f'Save dir {save_dir} is not empty! Deleting!'))
        if os.path.isdir(save_dir):
            shutil.rmtree(save_dir)
        else:
            os.remove(save_dir)


    # Copy project to a temporary directory 
    TMP_DIR1 = f'{save_dir}/orig_project'
    shutil.copytree(args.project_dir, TMP_DIR1, symlinks=True)
    project_dir = TMP_DIR1
    
    main_file   = args.main_file

    
    #   Many .tex files -> a single .tex file
    if args.flatten:
        main_file = flatten_tex(project_dir, main_file, args.remove_comments)

    # Remove files that not used in a compilation process
    if args.remove_redundant_files:
        TMP_DIR2 = f'{save_dir}/TMP_DIR2'
        remove_redundant_files(project_dir, main_file, save_dir=TMP_DIR2, debug=args.debug)
        project_dir = TMP_DIR2


        
    if args.flatten or args.convert_to_jpg:
        if args.flatten:
            print(blue('Flattening graphics...'))

        files = extract_graphics_paths(project_dir, main_file, args.debug, args.flatten)

        #  Change paths to images in the tex file
        
        if args.flatten:
            tex_files = [f'{project_dir}/main_flat.tex']
        else:
            tex_files = glob2.glob(f'{project_dir}/**/*.tex')
        for tex_file in tex_files:
            change_paths(tex_file, files, args.flatten, args.convert_to_jpg)
        
        # 5. Flatten files (copy files from subdirs to the main dir) or convert to rgb.
        flatten_convert_files(project_dir, files, args.flatten, args.convert_to_jpg, args.quality)


    # Copy form temporary directory to the target one
    for filename in os.listdir(project_dir):
        shutil.move(f'{project_dir}/{filename}', f'{save_dir}/{filename}')


    # Remove temp dirs
    shutil.rmtree(TMP_DIR1)
    if args.remove_redundant_files:
        shutil.rmtree(TMP_DIR2)


    print(green(f'Done! see ') + bold(save_dir))
    print(lightblue(f'KNOWN BUG: bibliography files are sometimes not copied. Check for them manually.'))





def replace_ext(x):
    ext = x.split('.')[-1]
    return x[:-len(ext)] + 'jpg' if ext.lower() in EXT else x


def identity(x):
    return x


def change_paths(tex_file, files, flatten, convert_to_jpg):
    '''
        Flattens paths: path/to/file.jpg -> ./file.jpg
    '''
    print(blue(f'Editing paths in {tex_file} {"and converting to .jpg" if convert_to_jpg else ""}'))

    with open(tex_file, 'r') as f:
        text = f.read()

    # 1. Try to match and replace full paths
    pattern = re.compile('|'.join(files))
    preprocessing = os.path.basename if flatten else identity
    postpocessing = replace_ext if convert_to_jpg else identity

    text, num = re.subn(pattern, lambda match: postpocessing(preprocessing(match.group())), text)
    
    if flatten:
        # Sometimes special symbols are used inside path, so let's try to find dir path
        dirnames_ = sorted(list(set([os.path.dirname(x) for x in files])))[::-1]
        for dir_path in dirnames_:
            pattern = re.compile(dir_path)
            text, num = re.subn(pattern, lambda match: '.', text)

    
    if convert_to_jpg:
        # 3. If we convert to jpg, then we need to change the extension in the basenames 
        pattern = re.compile('|'.join([os.path.basename(x) for x in files]))
        text, num = re.subn(pattern, lambda match: replace_ext(match.group()), text)

        # 4. Finally, let's fix all the rest by changing things like `.png` or `.tiff` to `.jpg`
        pattern = re.compile('|'.join([r'\.'+ x for x in EXT]))
        text, num = re.subn(pattern, lambda match: '.jpg', text)


    # Write down changed main
    with open(tex_file, 'w') as f:
        f.write(text)

def flatten_tex(project_dir, main_file, remove_comments):
    '''
        Many .tex files -> single .tex file main_flat.tex
    '''
    print(blue('Flattening TeX files using ') + yellow("latexpand"))

    os.system(f'cd {project_dir} && '\
              f'latexpand {"" if remove_comments else "--keep-comments"} {main_file} > {main_file[:-4]}_flat.tex')

    main_file = f'{main_file[:-4]}_flat.tex'

    return main_file

def remove_redundant_files(project_dir, main_file, save_dir, debug):
    '''
        `mkjobtexmf` will copy only the files that are actually used in the project, omitting others
        known problems: it does not copy .bib file
    '''
    print(blue('Removing redundant files using ' + yellow("mkjobtexmf")))
    
    tmp_dir = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    os.system(f'cd {project_dir} && '\
              f'mkjobtexmf --copy --jobname {main_file[:-4]} --cmd-tex pdflatex --destdir {tmp_dir} {"" if debug else ">/dev/null 2>&1"} && '\
              f'mv {tmp_dir} {os.path.abspath(save_dir)} && '\
              f'rm -R {os.path.abspath(save_dir)}/texmf')


    # Kind of fix
    for fname in sum([glob.glob(f'{project_dir}/*.{x}') for x in ['bib', 'bst']], []):
        shutil.copy(fname, save_dir)


def extract_graphics_paths(project_dir, main_file, debug, flatten):
    '''
        `latexmk` generates `fdb_latexmk` file with a list of used graphics files 
    '''
    print(blue('Extracting paths to graphics using ' + yellow('latexmk')))
    os.system(f'cd {project_dir} && '\
              f'latexmk {main_file} -pdf -dependents -recorder {"" if debug else "-quiet"}')

    '''
        Read `latexmk` file and the main file
    '''
    with open(f'{project_dir}/{main_file[:-4]}.fdb_latexmk', 'r') as f:
        fdb_latexmk_txt = f.read()

    # Get all the (sub)folders in the project directory
    files = []
    for r in next(os.walk(project_dir))[1]:
        files.extend(re.findall(r'  \"(%s.*?)\"' % r, fdb_latexmk_txt))
        
    # Check for duplicated basenames
    if flatten:
        basenames = [os.path.basename(x) for x in files]
        dups = set([x for x in basenames if basenames.count(x) > 1])
        if len(dups) > 0: 
            print(red('Found 2 different files with same basename, cannot flatten... Please fix.'))
            for d in dups:
                print([x for x in files if os.path.basename(x) == d])
            exit(1)



    return files


def flatten_convert_files(project_dir, files, flatten, convert_to_jpg, quality):
    for fpath in files:
        ext = fpath.split('.')[-1]

        new_path = fpath
        if flatten:
            new_path = os.path.basename(fpath)
            
        if convert_to_jpg and ext in EXT:
            new_path = new_path[:-len(ext)] + 'jpg'

        if new_path != fpath:
            if convert_to_jpg and ext in EXT:
                print(grey('Converting to .jpg  ') + red(f'{project_dir}/{fpath}'))
                Image.open(f'{project_dir}/{fpath}').convert('RGB').save(f'{project_dir}/{new_path}', quality=quality, optimize=True, progressive=True)
                os.remove(f'{project_dir}/{fpath}')
            else:
                shutil.copy(f'{project_dir}/{fpath}', f'{project_dir}/{os.path.basename(fpath)}')

    if flatten:
        # 6. Remove dir structure    
        for r in next(os.walk(project_dir))[1]:
            shutil.rmtree(f'{project_dir}/{r}')


if __name__ == "__main__":
    main()