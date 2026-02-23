import pandas as pd
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class LoadResult:
    data: Dict[str, pd.DataFrame]
    sheets: List[str]


def load_file(file) -> LoadResult:
    """
    Excel dosyasını yükler ve tüm sheetleri dataframe olarak döner
    """
    xls = pd.ExcelFile(file)
    data = {}

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        data[sheet] = df

    return LoadResult(
        data=data,
        sheets=xls.sheet_names
    )


def get_sheet_names(file) -> List[str]:
    """
    Excel sheet isimlerini döner
    """
    xls = pd.ExcelFile(file)
    return xls.sheet_names
