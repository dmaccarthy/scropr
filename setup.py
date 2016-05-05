from distutils.core import setup

setup(name="scropr", version="0.7a0", license = "GPLv3",
    packages = ["scropr"],
    package_data={"": ["icons/*.*", "robot/*.*"]},
    requires = ["pygame(>=1.9.1)"],

    # Author
    author = "David MacCarthy",
    author_email = "devwigs@gmail.com",

    # Details
    url = "http://dmaccarthy.github.io/scropr",
    description = "Create interactive animations in Python 3 (uses Pygame). Features inspied by Scratch, Processing, and robotics",
    long_description = open("README.txt").read()
)