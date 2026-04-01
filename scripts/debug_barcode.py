import io, traceback
import barcode
from barcode.writer import ImageWriter

tag='TEST-0001-26'
try:
    b = barcode.get('code128', tag, writer=ImageWriter())
    buf = io.BytesIO()
    b.write(buf, {'dpi': (72,72)})
    print('WROTE OK, size', buf.getbuffer().nbytes)
except Exception:
    traceback.print_exc()
