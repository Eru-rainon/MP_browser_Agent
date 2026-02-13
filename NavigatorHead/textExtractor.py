
from bs4 import BeautifulSoup,Tag
import os



class textExtractor():
    def __init__(self,embbedder):
        self.embedder = embbedder
        self.formattedText = []
        self.filePath = "extracted_text.txt"
        self.tooltip_attrs = ["uib-tooltip", "tooltip", "data-tooltip"]


    def getTextData(self,html):
        self.formattedText = []
        cleanedHTML = self.embedder.cleanHTML(html)
        soup = BeautifulSoup(cleanedHTML, 'lxml')
        for element in soup.body.descendants:

            tooltip = self.getToolTip(element) if isinstance(element, Tag) else None
            tooltipString = f"[Tooltio : {tooltip}]" if tooltip else ""

            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(element.name[1])
                self.appendLine(f"{'#' * level} {element.get_text(strip=True)}{tooltipString}")
            elif element.name == 'p':
                self.appendLine(f"\n{element.get_text(strip=True)}{tooltipString}\n")
            elif element.name == 'li':
                self.appendLine(f"- {element.get_text(strip=True)}{tooltipString}")
            elif element.name == 'label':
                self.appendLine(f"[Label] {element.get_text(strip=True)}{tooltipString}")
            elif element.name == 'span':
                self.appendLine(f"{element.get_text(strip=True)}{tooltipString}")
    
            elif element.name == 'table':
                self.appendLine(f"\n[Table]{tooltipString}")
            elif element.name == 'tr':
                row_data = [cell.get_text(strip=True) for cell in element.find_all(['td', 'th'])]
                self.appendLine(" | ".join(row_data))
                continue
            elif isinstance(element, str):
                text = f"{element.strip()}{tooltipString}"
                if text:
                    self.appendLine(text)
        finalText = '\n'.join(self.formattedText)

      
        if os.path.exists(self.filePath):
            with open(self.filePath, "a", encoding="utf-8") as file:
                file.write(finalText + "\n")
        else:
            with open(self.filePath, "a", encoding="utf-8") as file:
                file.write(finalText + "\n")

        return finalText.strip()




    def appendLine(self,line):
        if line and line.strip():
            line = line.strip()
            if line not in self.formattedText: 
                self.formattedText.append(line.strip())
        return

    def getToolTip(self,element):
        tooltips = []
        for attr in self.tooltip_attrs:
            val = element.get(attr)
            if val:
                tooltips.append(val)

        if tooltips:
            return " | ".join(tooltips)
        return None
    