export async function downloadElementAsPdf(element: HTMLElement, filename: string) {
  await document.fonts.ready;

  const [{ default: html2canvas }, { default: jsPDF }] = await Promise.all([
    import("html2canvas"),
    import("jspdf"),
  ]);

  const canvas = await html2canvas(element, {
    backgroundColor: "#faf8f5",
    logging: false,
    scale: 2,
    useCORS: true,
    windowWidth: element.scrollWidth,
    windowHeight: element.scrollHeight,
  });

  const pdf = new jsPDF({
    orientation: "portrait",
    unit: "mm",
    format: "a4",
    compress: true,
  });

  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const imageWidth = pageWidth;
  const imageHeight = (canvas.height * imageWidth) / canvas.width;
  const imageData = canvas.toDataURL("image/jpeg", 0.96);

  let remainingHeight = imageHeight;
  let imageTop = 0;

  pdf.addImage(imageData, "JPEG", 0, imageTop, imageWidth, imageHeight, undefined, "FAST");
  remainingHeight -= pageHeight;

  while (remainingHeight > 0) {
    imageTop -= pageHeight;
    pdf.addPage();
    pdf.addImage(imageData, "JPEG", 0, imageTop, imageWidth, imageHeight, undefined, "FAST");
    remainingHeight -= pageHeight;
  }

  pdf.save(filename);
}
