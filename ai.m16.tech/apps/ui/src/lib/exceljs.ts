import * as ExcelJS from "exceljs"
import { saveAs } from "file-saver"

async function saveFile (fileName: string, workbook: ExcelJS.Workbook) {
  const xls64 = await workbook.xlsx.writeBuffer()
  saveAs(
    new Blob([xls64], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }),
    fileName
  )
}

export async function arrayToXlsx(fileName: string, rows: any[]) {
  const workbook = new ExcelJS.Workbook();
  const sheet = workbook.addWorksheet('')
  sheet.addRows(rows)
  await saveFile(fileName, workbook)
}
