import sys
import semantic_version

sys.path.append('../')
from report import report_info

kubeOpenShiftVersionMap = {"1.13": "4.1",
                           "1.14": "4.2",
                           "1.16": "4.3",
                           "1.17": "4.4",
                           "1.18": "4.5",
                           "1.19": "4.6",
                           "1.20": "4.7",
                           "1.21": "4.8",
                           "1.22": "4.9"}


def getOCPVersions(kubeVersion):

    if kubeVersion == "":
        return "N/A"

    checkKubeVersion = kubeVersion

    try:
        semantic_version.NpmSpec(kubeVersion)
    except ValueError:
        print(f"Value error with kubeVersion -  NpmSpec : {kubeVersion}, see if it fixable")

        try:
            # Kubversion is bad, see if we can fix it
            separator = checkKubeVersion.find(" - ")
            if separator != -1:
                lowVersion = checkKubeVersion[:separator].strip()
                highVersion = checkKubeVersion[separator+3:].strip()
                checkKubeVersion = f"{semantic_version.Version.coerce(lowVersion)} - {semantic_version.Version.coerce(highVersion)}"
            else:
                firstDigit = -1
                for i, c in enumerate(checkKubeVersion):
                    if c.isdigit():
                        firstDigit = i
                        break
                if firstDigit != -1:
                    versionInRange = checkKubeVersion[firstDigit:].strip()
                    preVersion = checkKubeVersion[:firstDigit].strip()
                    checkKubeVersion = f"{preVersion}{semantic_version.Version.coerce(versionInRange)}"

            # see if the updates have helped
            semantic_version.NpmSpec(checkKubeVersion)
            print(f"Fixed value error in kubeVersion : {checkKubeVersion}")

        except ValueError:
            print(f"Unable to fix value error in kubeVersion : {kubeVersion}")
            return "N/A"


    minOCP = ""
    maxOCP = ""
    for kubeVersionKey in kubeOpenShiftVersionMap :
        coercedKubeVersionKey = semantic_version.Version.coerce(kubeVersionKey)
        if minOCP == "" and coercedKubeVersionKey in semantic_version.NpmSpec(checkKubeVersion):
            minOCP = kubeOpenShiftVersionMap[kubeVersionKey]
            print(f"   Found min : {kubeVersion}: {minOCP}")
        elif coercedKubeVersionKey in semantic_version.NpmSpec(checkKubeVersion):
            maxOCP = kubeOpenShiftVersionMap[kubeVersionKey]
            print(f"   Found new Max : {kubeVersion}: {maxOCP}")

    # check if minOCP is open ended
    if minOCP != "" and semantic_version.Version("1.999.999") in semantic_version.NpmSpec(checkKubeVersion):
        ocp_versions = f">={minOCP}"
    elif minOCP == "":
        ocp_versions = "N/A"
    elif maxOCP == "":
        ocp_versions = minOCP
    else:
        ocp_versions = f"{minOCP} - {maxOCP}"

    return ocp_versions


def getIndexAnnotations(report_path):

    annotations = report_info.get_report_annotations(report_path)

    set_annotations = {}
    OCPSupportedSet = False
    for annotation in annotations:
        if annotation == "charts.openshift.io/certifiedOpenShiftVersions":
            full_version = annotations[annotation]
            if full_version != "N/A" and semantic_version.validate(full_version):
                ver = semantic_version.Version(full_version)
                set_annotations["charts.openshift.io/testedOpenShiftVersion"] = f"{ver.major}.{ver.minor}"
            else:
                set_annotations["charts.openshift.io/testedOpenShiftVersion"] = annotations[annotation]
        else:
            if annotation == "charts.openshift.io/supportedOpenShiftVersions":
                OCPSupportedSet = True
            set_annotations[annotation] = annotations[annotation]

    if not OCPSupportedSet:
        chart = report_info.get_report_chart(report_path)
        OCPVersions = "N/A"
        if "kubeVersion" in chart and chart["kubeVersion"]:
            kubeVersion = chart["kubeVersion"]
            OCPVersions = getOCPVersions(kubeVersion)
        set_annotations["charts.openshift.io/supportedOpenShiftVersions"] = OCPVersions

    return set_annotations
