import re
from copy import deepcopy
import logging
from fgt_transposer.exceptions import SectionOrVdomException

log_msg = logging.getLogger(f"priLogger.{__name__}")


class Parser:
    def __init__(self, dstfile, srcfile, newfile, capture, swapheaders):
        self.files_as_dict = {
            "dstfile": dstfile,
            "srcfile": srcfile,
        }
        self.vdoms_dict_results = {"dstfile": {}, "srcfile": {}}
        """ final vdoms_dict_results looks like:
                {"dstfile": [{header},{vdoms},{config_global},{vdomname1}, {vdomname2}], 
                "srcfile": [{header},{vdoms},{config_global},{vdomname1}, {vdomname2}]},
                "newfile": <copy of dstfile data>
        """
        self.newfile_name = newfile
        self.arguments = capture
        self.swapheaders = swapheaders

    @staticmethod
    def return_files_as_vars(arguments) -> dict:
        """Converts files to str vars separated by \n"""
        dstconf = arguments["dstconf"]
        srcconf = arguments["srcconf"]
        with open(dstconf, "r") as dstconfig:
            data_dst = dstconfig.read()
        with open(srcconf, "r") as srcconfig:
            data_src = srcconfig.read()
        return {
            "dstfile": data_dst,
            "srcfile": data_src,
            "newfile": f"{dstconf}_transposed.conf",
            "capture": arguments["Capture"],
            "swapheaders": arguments["swapheaders"],
        }

    def regex_storage(
        self,
        full_vdom=False,
        full_vdom_name=None,
        header=False,
        vdom_header=False,
        cglobal=False,
        yamlend=False,
        yamlnext=False,
        start=None,
        stop=None,
    ) -> str:
        """Stores all regex expressions used by parser"""
        if full_vdom:
            return f"(?s)(?<=^end$\n^end$\n)\n?config vdom$\nedit {full_vdom_name}.+?^end$\n^end$\n?"
        if header:
            return r"(?s)(?<=)^#.+?(?=\n?^config vdom$)"
        if vdom_header:
            return r"(?s)(?<=)config vdom$.+?^next$\n^end$\n?"
        if cglobal:
            return r"(?s)(?<=^next$\n^end$\n)\n?config global$.+?^end$\n^end$\n?"
        if yamlend:
            return r"(?s)(?<=)" + start + "$.+?^" + stop + "$"
        if yamlnext:
            return r"(?s)(?<=)" + start + "$.+?" + stop + "$"

    def update_results_dictionary(self, filename, dictdata):
        self.vdoms_dict_results[filename].update(dictdata)

    def grab_regex_value(self, parameter, filedata, full_vdom_name=None):
        if full_vdom_name:
            parameter = {parameter: True, "full_vdom_name": full_vdom_name}
        else:
            parameter = {parameter: True}
        regex_string = self.regex_storage(**parameter)
        regex_compiled = re.compile(regex_string, re.MULTILINE)
        regex_results = re.findall(regex_compiled, filedata)
        return regex_results

    def grab_headers(self, filename, filedata):
        """Grabs all header info including config global. Appends to self.vdoms_dict_results"""
        header = self.grab_regex_value("header", filedata)
        vdom_header = self.grab_regex_value("vdom_header", filedata)
        cglobal = self.grab_regex_value("cglobal", filedata)
        self.update_results_dictionary(filename, {"header": header})
        self.update_results_dictionary(filename, {"vdoms": vdom_header})
        self.update_results_dictionary(filename, {"config_global": cglobal})

    def grab_vdom_names(self, filename) -> list:
        """Parses out vdom names from file
        :param file var
        :return list of vdom names
        """
        unacceptable_vdom_names = ["config", "vdom", "next", "edit", "end"]
        vdoms_unformatted = self.vdoms_dict_results[filename]["vdoms"][0]
        if vdoms_unformatted:
            vdoms_list = []
            for i in vdoms_unformatted.split():
                if i not in unacceptable_vdom_names:
                    vdoms_list.append(i)
            return vdoms_list

    def grab_vdoms_full(self, filename, filedata, vdomnames):
        """Constructs per vdom dictionary self.vdoms_dict_results"""
        for vdom in vdomnames:
            full_vdom = self.grab_regex_value(
                "full_vdom", filedata, full_vdom_name=vdom
            )
            self.update_results_dictionary(filename, {vdom: full_vdom})

    def find_and_replace(self, two_file_dict, arguments):
        """Transposes sections of config"""
        dstfile = two_file_dict["dstfile"]
        srcfile = two_file_dict["srcfile"]
        newfile = deepcopy(dstfile)
        for far in arguments:
            log_msg.debug(f"Searching for: {far}")
            start = far.get("Start")
            stop = far.get("Stop")
            wipe = far.get("Wipe")
            sectionorvdom = far.get("SectionOrVdom")
            if not sectionorvdom:
                raise SectionOrVdomException(f"No SectionOrVdom given for {start} / {stop}")
            if start is not None and stop is not None and "end" in stop:
                regex_query = self.regex_storage(yamlend=True, start=start, stop=stop)
            elif start is not None and stop is not None:
                regex_query = self.regex_storage(yamlnext=True, start=start, stop=stop)
            compiled_regex = re.compile(regex_query, re.MULTILINE)
            dstFoundRegex = re.findall(compiled_regex, dstfile[sectionorvdom][0])
            srcFoundRegex = re.findall(compiled_regex, srcfile[sectionorvdom][0])
            replacement_results = None
            if wipe:
                wipe_string = f"{start}\n{stop}"
                replacement_results = re.sub(
                    regex_query, wipe_string, newfile[sectionorvdom][0], flags=re.M
                )
                log_msg.info(f"Wiped: {regex_query}")
            elif dstFoundRegex and srcFoundRegex:
                log_msg.info(f"Found :{dstFoundRegex=}, {srcFoundRegex=}")
                replacement_results = re.sub(
                    regex_query, srcFoundRegex[0], newfile[sectionorvdom][0], flags=re.M
                )
            else:
                log_msg.warning(
                    f"Section not found: {start=}, {stop=}"
                )
            if replacement_results:
                newfile[sectionorvdom][0] = replacement_results
            if self.swapheaders:
                newfile["header"] = self.vdoms_dict_results["srcfile"]["header"]
        self.vdoms_dict_results.update({"newfile": newfile})

    def run_parse(self):
        """:return dictionary of dstfile, srcfile, newfile for writing to file"""
        for k, v in self.files_as_dict.items():
            self.grab_headers(k, v)
            self.grab_vdoms_full(k, v, self.grab_vdom_names(k))
        self.find_and_replace(self.vdoms_dict_results, self.arguments)
        return self.newfile_name, self.vdoms_dict_results["newfile"]
