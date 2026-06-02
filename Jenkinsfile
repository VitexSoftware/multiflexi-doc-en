#!groovy

String[] distributions = [
    'debian:bookworm',
    'debian:trixie',
    'ubuntu:jammy',
    'ubuntu:noble'
]

String vendor = 'vitexsoftware'

properties([
    copyArtifactPermission('*'),
    buildBlocker(
        useBuildBlocker: true,
        blockLevel: 'GLOBAL',
        scanQueueFor: 'ALL',
        blockingJobs: 'RebulidDEBRepoByAnsible'
    )
])

node() {
    ansiColor('xterm') {
        stage('SCM Checkout') {
            checkout scm
        }
    }
}

def branches = [:]

distributions.each { distro ->
    branches[distro] = {
        def dist = distro.split(':')
        def distroCode = dist[1]
        def buildImage = ''
        def artifacts = []
        def buildVer = ''

        node {
            ansiColor('xterm') {
                stage('Checkout ' + distro) {
                    checkout scm
                    buildImage = docker.image(vendor + '/' + distro)
                    sh 'git checkout debian/changelog'
                    def version = sh(
                        script: 'dpkg-parsechangelog --show-field Version',
                        returnStdout: true
                    ).trim()
                    buildVer = version + '.' + env.BUILD_NUMBER + '~' + distroCode
                }

                stage('Build ' + distro) {
                    buildImage.inside {
                        sh 'dch -b -v ' + buildVer + ' "' + env.BUILD_TAG + '"'
                        sh 'sudo apt-get update --allow-releaseinfo-change'
                        sh 'sudo chown jenkins:jenkins ..'
                        sh 'debuild-pbuilder -i -us -uc -b'
                        sh 'mkdir -p $WORKSPACE/dist/debian/ ; rm -rf $WORKSPACE/dist/debian/* ; for deb in $(cat debian/files | awk \'{print $1}\'); do mv "../$deb" $WORKSPACE/dist/debian/; done'
                        artifacts = sh(
                            script: "cat debian/files | awk '{print \$1}'",
                            returnStdout: true
                        ).trim().split('\n')
                    }
                }

                stage('Test ' + distro) {
                    buildImage.inside {
                        sh 'cd $WORKSPACE/dist/debian/ ; dpkg-scanpackages . /dev/null > Packages; gzip -9c Packages > Packages.gz; cd $WORKSPACE'
                        sh 'echo "deb [trusted=yes] file://///$WORKSPACE/dist/debian/ ./" | sudo tee /etc/apt/sources.list.d/local.list'
                        sh 'sudo apt-get update --allow-releaseinfo-change'
                        artifacts.each { deb_file ->
                            if (deb_file.endsWith('.deb')) {
                                def pkgName = deb_file.tokenize('/')[-1].replaceFirst(/_.*/, '')
                                sh 'sudo DEBIAN_FRONTEND=noninteractive apt-get -y install ' + pkgName + ' || sudo apt-get -y -f install'
                            }
                        }
                    }
                }

                stage('Archive ' + distro) {
                    buildImage.inside {
                        artifacts.each { deb_file ->
                            archiveArtifacts artifacts: 'dist/debian/' + deb_file
                        }
                        sh '''
                            if [ -f debian/files ]; then
                              while read -r file _; do
                                [ -n "$file" ] || continue
                                rm -f "dist/debian/$file" "../../$file" || true
                              done < debian/files
                            fi
                        '''
                    }
                }
            }
        }
    }
}

parallel branches

if (!currentBuild.result || currentBuild.result == 'SUCCESS') {
    build job: 'MultiFlexi-publish',
        wait: false,
        parameters: [
            string(name: 'UPSTREAM_JOB',    value: env.JOB_NAME),
            string(name: 'UPSTREAM_BUILD',  value: env.BUILD_NUMBER),
            string(name: 'REMOTE_SSH',      value: 'multirepo@repo.multiflexi.eu'),
            string(name: 'REMOTE_REPO_DIR', value: '/var/lib/multirepo/public/multiflexi'),
            string(name: 'COMPONENT',       value: 'main'),
            string(name: 'DEB_DIST',        value: '')
        ]
}
