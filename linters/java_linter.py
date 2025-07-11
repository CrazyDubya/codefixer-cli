"""
Java linter module using PMD and Checkstyle.
"""

import os
import subprocess
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from .env_manager import EnvironmentManager


class JavaLinter:
    """Java linter using PMD and Checkstyle."""
    
    def __init__(self, env_manager: EnvironmentManager):
        self.env_manager = env_manager
        self.linter_name = "pmd-checkstyle"
        
    def setup_environment(self, repo_path: str) -> str:
        """Set up Java environment with PMD and Checkstyle."""
        env_path = self.env_manager.get_env_path(repo_path, "java")
        
        if not self.env_manager.env_exists(env_path):
            self.env_manager.create_env(env_path)
            
            # Download PMD
            try:
                subprocess.run([
                    "curl", "-L", "-o", "pmd-bin.zip",
                    "https://github.com/pmd/pmd/releases/latest/download/pmd-bin-7.0.0.zip"
                ], cwd=env_path, check=True, capture_output=True)
                
                subprocess.run([
                    "unzip", "-q", "pmd-bin.zip"
                ], cwd=env_path, check=True, capture_output=True)
                
                # Rename extracted directory
                subprocess.run([
                    "mv", "pmd-bin-*", "pmd"
                ], cwd=env_path, check=True, capture_output=True)
                
            except subprocess.CalledProcessError:
                raise RuntimeError("Failed to install PMD")
        
        return env_path
    
    def create_pmd_config(self, repo_path: str) -> str:
        """Create PMD configuration file."""
        config_content = """<?xml version="1.0"?>
<ruleset name="CodeFixer PMD Rules"
         xmlns="http://pmd.sourceforge.net/ruleset/2.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://pmd.sourceforge.net/ruleset/2.0.0 https://pmd.sourceforge.io/ruleset_2_0_0.xsd">

    <description>
        PMD rules for CodeFixer Java linting
    </description>

    <!-- Include all rules -->
    <rule ref="category/java/bestpractices.xml"/>
    <rule ref="category/java/codestyle.xml"/>
    <rule ref="category/java/design.xml"/>
    <rule ref="category/java/documentation.xml"/>
    <rule ref="category/java/errorprone.xml"/>
    <rule ref="category/java/multithreading.xml"/>
    <rule ref="category/java/performance.xml"/>
    <rule ref="category/java/security.xml"/>

    <!-- Exclude some overly strict rules -->
    <rule ref="category/java/codestyle.xml/AtLeastOneConstructor">
        <priority>4</priority>
    </rule>
    <rule ref="category/java/codestyle.xml/OnlyOneReturn">
        <priority>4</priority>
    </rule>
    <rule ref="category/java/codestyle.xml/TooManyStaticImports">
        <priority>4</priority>
    </rule>

    <!-- Exclude test files -->
    <exclude-pattern>**/test/**</exclude-pattern>
    <exclude-pattern>**/tests/**</exclude-pattern>
    <exclude-pattern>**/*Test.java</exclude-pattern>
    <exclude-pattern>**/*Tests.java</exclude-pattern>

</ruleset>
"""
        
        config_path = os.path.join(repo_path, "pmd-ruleset.xml")
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        return config_path
    
    def create_checkstyle_config(self, repo_path: str) -> str:
        """Create Checkstyle configuration file."""
        config_content = """<?xml version="1.0"?>
<!DOCTYPE module PUBLIC
          "-//Checkstyle//DTD Checkstyle Configuration 1.3//EN"
          "https://checkstyle.org/dtds/configuration_1_3.dtd">

<module name="Checker">
    <property name="charset" value="UTF-8"/>
    <property name="severity" value="warning"/>
    <property name="fileExtensions" value="java, properties, xml"/>

    <!-- Exclude test files -->
    <module name="BeforeExecutionExclusionFileFilter">
        <property name="fileNamePattern" value=".*[/\\\\]test[/\\\\].*"/>
    </module>
    <module name="BeforeExecutionExclusionFileFilter">
        <property name="fileNamePattern" value=".*Test\\.java$"/>
    </module>
    <module name="BeforeExecutionExclusionFileFilter">
        <property name="fileNamePattern" value=".*Tests\\.java$"/>
    </module>

    <!-- TreeWalker -->
    <module name="TreeWalker">
        <!-- Naming -->
        <module name="ConstantName"/>
        <module name="LocalFinalVariableName"/>
        <module name="LocalVariableName"/>
        <module name="MemberName"/>
        <module name="MethodName"/>
        <module name="PackageName"/>
        <module name="ParameterName"/>
        <module name="StaticVariableName"/>
        <module name="TypeName"/>

        <!-- Imports -->
        <module name="AvoidStarImport"/>
        <module name="IllegalImport"/>
        <module name="RedundantImport"/>
        <module name="UnusedImports"/>

        <!-- Size Violations -->
        <module name="MethodLength">
            <property name="max" value="150"/>
        </module>
        <module name="ParameterNumber">
            <property name="max" value="7"/>
        </module>

        <!-- Whitespace -->
        <module name="EmptyForIteratorPad"/>
        <module name="GenericWhitespace"/>
        <module name="MethodParamPad"/>
        <module name="NoWhitespaceAfter"/>
        <module name="NoWhitespaceBefore"/>
        <module name="OperatorWrap"/>
        <module name="ParenPad"/>
        <module name="TypecastParenPad"/>
        <module name="WhitespaceAfter"/>
        <module name="WhitespaceAround"/>

        <!-- Modifiers -->
        <module name="ModifierOrder"/>
        <module name="RedundantModifier"/>

        <!-- Blocks -->
        <module name="AvoidNestedBlocks"/>
        <module name="EmptyBlock"/>
        <module name="LeftCurly"/>
        <module name="NeedBraces"/>
        <module name="RightCurly"/>

        <!-- Coding Problems -->
        <module name="EmptyStatement"/>
        <module name="EqualsHashCode"/>
        <module name="HiddenField">
            <property name="ignoreSetter" value="true"/>
            <property name="ignoreConstructorParameter" value="true"/>
        </module>
        <module name="IllegalInstantiation"/>
        <module name="InnerAssignment"/>
        <module name="MagicNumber"/>
        <module name="MissingSwitchDefault"/>
        <module name="MultipleVariableDeclarations"/>
        <module name="SimplifyBooleanExpression"/>
        <module name="SimplifyBooleanReturn"/>

        <!-- Class Design -->
        <module name="DesignForExtension"/>
        <module name="FinalClass"/>
        <module name="HideUtilityClassConstructor"/>
        <module name="InterfaceIsType"/>
        <module name="VisibilityModifier"/>

        <!-- Finalizer -->
        <module name="NoFinalizer"/>

        <!-- Miscellaneous -->
        <module name="ArrayTypeStyle"/>
        <module name="FinalParameters"/>
        <module name="TodoComment"/>
        <module name="UpperEll"/>

    </module>
</module>
"""
        
        config_path = os.path.join(repo_path, "checkstyle.xml")
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        return config_path
    
    def lint_files(self, repo_path: str, files: List[str]) -> List[Dict[str, Any]]:
        """Lint Java files using PMD and Checkstyle."""
        if not files:
            return []
        
        env_path = self.setup_environment(repo_path)
        pmd_config = self.create_pmd_config(repo_path)
        checkstyle_config = self.create_checkstyle_config(repo_path)
        
        issues = []
        
        # Run PMD
        try:
            pmd_script = os.path.join(env_path, "pmd", "bin", "pmd")
            if os.name == 'nt':  # Windows
                pmd_script += ".bat"
            
            result = subprocess.run([
                pmd_script, "check",
                "-d", repo_path,
                "-R", pmd_config,
                "-f", "json"
            ], cwd=repo_path, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                try:
                    pmd_output = json.loads(result.stdout)
                    for file_issue in pmd_output.get("files", []):
                        file_path = file_issue.get("filename", "")
                        if file_path and any(f in file_path for f in files):
                            for violation in file_issue.get("violations", []):
                                issues.append({
                                    "file": file_path,
                                    "line": violation.get("beginline", 0),
                                    "column": violation.get("begincolumn", 0),
                                    "message": violation.get("description", ""),
                                    "code": violation.get("rule", ""),
                                    "severity": self._map_pmd_severity(violation.get("priority", 3)),
                                    "category": self._categorize_pmd_issue(violation.get("rule", ""))
                                })
                except json.JSONDecodeError:
                    pass
        
        except subprocess.TimeoutExpired:
            raise RuntimeError("PMD timed out")
        except Exception as e:
            # PMD failed, continue with Checkstyle
            pass
        
        # Run Checkstyle (if available)
        try:
            result = subprocess.run([
                "java", "-jar", "checkstyle.jar",
                "-c", checkstyle_config,
                "-f", "xml",
                repo_path
            ], cwd=env_path, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                try:
                    root = ET.fromstring(result.stdout)
                    for file_elem in root.findall(".//file"):
                        file_path = file_elem.get("name", "")
                        if file_path and any(f in file_path for f in files):
                            for error in file_elem.findall(".//error"):
                                issues.append({
                                    "file": file_path,
                                    "line": int(error.get("line", 0)),
                                    "column": int(error.get("column", 0)),
                                    "message": error.get("message", ""),
                                    "code": error.get("source", ""),
                                    "severity": self._map_checkstyle_severity(error.get("severity", "warning")),
                                    "category": self._categorize_checkstyle_issue(error.get("source", ""))
                                })
                except ET.ParseError:
                    pass
        
        except Exception as e:
            # Checkstyle failed, continue with PMD results only
            pass
        
        return issues
    
    def _map_pmd_severity(self, priority: int) -> str:
        """Map PMD priority to standard severity."""
        if priority <= 1:
            return "high"
        elif priority <= 2:
            return "medium"
        else:
            return "low"
    
    def _map_checkstyle_severity(self, severity: str) -> str:
        """Map Checkstyle severity to standard severity."""
        severity_map = {
            "error": "high",
            "warning": "medium",
            "info": "low"
        }
        return severity_map.get(severity.lower(), "medium")
    
    def _categorize_pmd_issue(self, rule: str) -> str:
        """Categorize PMD issue based on rule."""
        security_rules = {"security"}
        performance_rules = {"performance"}
        style_rules = {"codestyle"}
        
        rule_lower = rule.lower()
        if any(sec in rule_lower for sec in security_rules):
            return "security"
        elif any(perf in rule_lower for perf in performance_rules):
            return "performance"
        elif any(style in rule_lower for style in style_rules):
            return "formatting"
        else:
            return "code_quality"
    
    def _categorize_checkstyle_issue(self, source: str) -> str:
        """Categorize Checkstyle issue based on source."""
        if "naming" in source.lower():
            return "formatting"
        elif "imports" in source.lower():
            return "code_quality"
        elif "whitespace" in source.lower():
            return "formatting"
        else:
            return "code_quality" 