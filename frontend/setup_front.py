import subprocess

proc = subprocess.Popen(['sass',"static/styles/scss/styles.scss","static/styles/styles.css","--style","compressed"], shell=True)
proc.communicate()