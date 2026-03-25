from __future__ import annotations

import math
import operator
from dataclasses import replace

import polars as pl

from portakal_app.data.models import DatasetHandle, build_data_domain

# Safe built-in functions available in formula expressions
_SAFE_BUILTINS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "len": len,
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
}

_SAFE_MATH = {
    "sqrt": math.sqrt,
    "log": math.log,
    "log2": math.log2,
    "log10": math.log10,
    "exp": math.exp,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pi": math.pi,
    "e": math.e,
    "ceil": math.ceil,
    "floor": math.floor,
    "pow": math.pow,
}


class FormulaService:
    def apply_formulas(
        self,
        dataset: DatasetHandle,
        *,
        formulas: list[tuple[str, str]],
    ) -> DatasetHandle:
        """Apply a list of (column_name, expression_string) formulas to the dataset.

        Each expression is evaluated as a Polars expression using the existing columns.
        Supported patterns:
          - Column references: col_name (directly by name)
          - Arithmetic: +, -, *, /, //, %, **
          - Math functions: sqrt, log, sin, cos, etc.
          - Comparisons: >, <, >=, <=, ==, !=
          - String concatenation with +
        """
        df = dataset.dataframe

        if not formulas:
            return dataset

        for col_name, expr_str in formulas:
            col_name = col_name.strip()
            expr_str = expr_str.strip()
            if not col_name or not expr_str:
                continue
            try:
                expr = _parse_formula(expr_str, df.columns)
                df = df.with_columns(expr.alias(col_name))
            except Exception:
                df = df.with_columns(pl.lit(None).alias(col_name))

        return replace(
            dataset,
            dataset_id=f"{dataset.dataset_id}-formula",
            display_name=f"{dataset.display_name} (formula)",
            dataframe=df,
            row_count=df.height,
            column_count=df.width,
            domain=build_data_domain(df),
        )


def _parse_formula(expr_str: str, columns: list[str]) -> pl.Expr:
    """Parse a formula string into a Polars expression.

    Uses a safe eval approach with only column references and math operations.
    """
    namespace: dict = {}
    namespace.update(_SAFE_BUILTINS)
    namespace.update(_SAFE_MATH)

    # Add polars column references
    for col_name in columns:
        safe_name = col_name.replace(" ", "_").replace("-", "_")
        namespace[safe_name] = pl.col(col_name)
        # Also allow original name if different
        if safe_name != col_name:
            namespace[col_name] = pl.col(col_name)

    # Add polars utility
    namespace["col"] = pl.col
    namespace["lit"] = pl.lit
    namespace["when"] = pl.when

    # Restrict to safe operations
    namespace["__builtins__"] = {}

    result = eval(expr_str, namespace)  # noqa: S307
    if isinstance(result, pl.Expr):
        return result
    return pl.lit(result)
