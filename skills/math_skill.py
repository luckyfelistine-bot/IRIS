"""IRIS v8 Aevibron Math Skill — Precision Mathematics with SymPy"""
import os
import json
from typing import Dict, Any, Optional
from config import config

class MathSkill:
    """
    Aevibron Math — IRIS's precision mathematics engine:
    - Symbolic computation (algebra, calculus)
    - Numerical precision (arbitrary precision)
    - Equation solving
    - Matrix operations
    - Statistics
    - Unit conversions
    - Step-by-step solutions
    """

    def __init__(self):
        self._sympy_available = False
        self._numpy_available = False
        self._init_libraries()

    def _init_libraries(self):
        try:
            import sympy as sp
            self.sp = sp
            self._sympy_available = True
        except ImportError:
            self.sp = None

        try:
            import numpy as np
            self.np = np
            self._numpy_available = True
        except ImportError:
            self.np = None

    def solve(self, expression: str, variable: str = "x") -> Dict:
        """Solve an equation or expression."""
        if not self._sympy_available:
            return {"success": False, "error": "SymPy not installed. Run: pip install sympy"}

        try:
            x = self.sp.Symbol(variable)
            # Try to parse as equation first
            if "=" in expression:
                lhs, rhs = expression.split("=", 1)
                eq = self.sp.Eq(self.sp.sympify(lhs.strip()), self.sp.sympify(rhs.strip()))
                solutions = self.sp.solve(eq, x)
            else:
                expr = self.sp.sympify(expression)
                solutions = self.sp.solve(expr, x)

            # Format solutions
            formatted = []
            for sol in solutions if isinstance(solutions, list) else [solutions]:
                formatted.append(str(sol))

            return {
                "success": True,
                "expression": expression,
                "solutions": formatted,
                "latex": self.sp.latex(solutions) if hasattr(solutions, '__iter__') else str(solutions),
                "message": f"Solution{'s' if len(formatted) > 1 else ''}: {', '.join(formatted)}"
            }
        except Exception as e:
            return {"success": False, "error": str(e), "expression": expression}

    def simplify(self, expression: str) -> Dict:
        """Simplify a mathematical expression."""
        if not self._sympy_available:
            return {"success": False, "error": "SymPy not installed"}

        try:
            expr = self.sp.sympify(expression)
            simplified = self.sp.simplify(expr)
            expanded = self.sp.expand(expr)
            factored = self.sp.factor(expr)

            return {
                "success": True,
                "original": expression,
                "simplified": str(simplified),
                "expanded": str(expanded),
                "factored": str(factored),
                "latex_simplified": self.sp.latex(simplified)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def differentiate(self, expression: str, variable: str = "x", order: int = 1) -> Dict:
        """Compute derivative."""
        if not self._sympy_available:
            return {"success": False, "error": "SymPy not installed"}

        try:
            x = self.sp.Symbol(variable)
            expr = self.sp.sympify(expression)
            derivative = self.sp.diff(expr, x, order)

            return {
                "success": True,
                "original": expression,
                "derivative": str(derivative),
                "order": order,
                "variable": variable,
                "latex": self.sp.latex(derivative),
                "message": f"d^{order}/d{variable}^{order} ({expression}) = {derivative}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def integrate(self, expression: str, variable: str = "x", limits: tuple = None) -> Dict:
        """Compute integral (definite or indefinite)."""
        if not self._sympy_available:
            return {"success": False, "error": "SymPy not installed"}

        try:
            x = self.sp.Symbol(variable)
            expr = self.sp.sympify(expression)

            if limits:
                a, b = limits
                result = self.sp.integrate(expr, (x, a, b))
                return {
                    "success": True,
                    "original": expression,
                    "integral": str(result),
                    "type": "definite",
                    "limits": limits,
                    "latex": self.sp.latex(result)
                }
            else:
                result = self.sp.integrate(expr, x)
                return {
                    "success": True,
                    "original": expression,
                    "integral": str(result) + " + C",
                    "type": "indefinite",
                    "latex": self.sp.latex(result)
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def matrix_ops(self, operation: str, matrices: list) -> Dict:
        """Matrix operations: multiply, invert, determinant, eigenvalues."""
        if not self._sympy_available:
            return {"success": False, "error": "SymPy not installed"}

        try:
            mats = [self.sp.Matrix(m) for m in matrices]

            if operation == "multiply":
                result = mats[0]
                for m in mats[1:]:
                    result = result * m
                return {"success": True, "operation": operation, "result": str(result), "shape": result.shape}

            elif operation == "inverse":
                result = mats[0].inv()
                return {"success": True, "operation": operation, "result": str(result), "shape": result.shape}

            elif operation == "determinant":
                result = mats[0].det()
                return {"success": True, "operation": operation, "result": str(result)}

            elif operation == "eigenvalues":
                result = mats[0].eigenvals()
                return {"success": True, "operation": operation, "result": {str(k): str(v) for k, v in result.items()}}

            elif operation == "rank":
                result = mats[0].rank()
                return {"success": True, "operation": operation, "result": str(result)}

            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def statistics(self, data: list, operation: str = "all") -> Dict:
        """Statistical analysis."""
        if not self._numpy_available:
            return {"success": False, "error": "NumPy not installed"}

        try:
            arr = self.np.array(data)
            results = {"data_points": len(data)}

            if operation in ["all", "mean"]:
                results["mean"] = float(self.np.mean(arr))
            if operation in ["all", "median"]:
                results["median"] = float(self.np.median(arr))
            if operation in ["all", "std"]:
                results["std"] = float(self.np.std(arr))
            if operation in ["all", "variance"]:
                results["variance"] = float(self.np.var(arr))
            if operation in ["all", "min"]:
                results["min"] = float(self.np.min(arr))
            if operation in ["all", "max"]:
                results["max"] = float(self.np.max(arr))
            if operation in ["all", "sum"]:
                results["sum"] = float(self.np.sum(arr))

            return {"success": True, "operation": operation, "results": results}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def convert_units(self, value: float, from_unit: str, to_unit: str) -> Dict:
        """Convert between units using SymPy's unit system."""
        if not self._sympy_available:
            return {"success": False, "error": "SymPy not installed"}

        try:
            # Common conversions
            conversions = {
                ("m", "km"): 0.001, ("km", "m"): 1000,
                ("cm", "m"): 0.01, ("m", "cm"): 100,
                ("g", "kg"): 0.001, ("kg", "g"): 1000,
                ("lb", "kg"): 0.453592, ("kg", "lb"): 2.20462,
                ("c", "f"): lambda x: x * 9/5 + 32,
                ("f", "c"): lambda x: (x - 32) * 5/9,
                ("c", "k"): lambda x: x + 273.15,
                ("k", "c"): lambda x: x - 273.15,
            }

            key = (from_unit.lower(), to_unit.lower())
            if key in conversions:
                conv = conversions[key]
                if callable(conv):
                    result = conv(value)
                else:
                    result = value * conv
                return {
                    "success": True,
                    "original": f"{value} {from_unit}",
                    "converted": f"{result:.6f} {to_unit}",
                    "value": result
                }
            else:
                return {"success": False, "error": f"Conversion from {from_unit} to {to_unit} not supported"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def evaluate(self, expression: str) -> Dict:
        """Safely evaluate a mathematical expression."""
        try:
            # Use SymPy for safe evaluation
            if self._sympy_available:
                expr = self.sp.sympify(expression)
                result = float(expr.evalf())
                return {
                    "success": True,
                    "expression": expression,
                    "result": result,
                    "exact": str(expr.evalf())
                }
            else:
                # Fallback: very restricted eval
                allowed = {"__builtins__": {}}
                result = eval(expression, allowed, {"abs": abs, "round": round, "max": max, "min": min, "sum": sum})
                return {"success": True, "expression": expression, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e), "expression": expression}

# Singleton
math_skill = MathSkill()
