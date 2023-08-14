import quilt3

if __name__ == "__main__":
    quilt3.Package().set('README.md', 'install.md').set('benchling_packager.yaml', 'build/benchling_packager.yaml').push('examples/benchling-packager', 's3://quilt-example')
